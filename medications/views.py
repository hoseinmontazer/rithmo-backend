from django.shortcuts import render
from rest_framework import viewsets , status
from rest_framework.response import Response
from .models import (   MedicationType ,
                        Medication ,
                        UserMedication ,
                        MedicationLog,
                        MedicationReminder
                    )
from .serializers import (  MedicationTypeSerializer,
                            MedicationSerializer,
                            UserMedicationSerializer,
                            MedicationLogSerializer,
                            MedicationReminderSerializer
                         )
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q
import requests
import re






def get_first(item, key, default=""):
    value = item.get(key, [])
    if isinstance(value, list) and value:
        return value[0]
    return default

def extract_dosages(text):
    if not text:
        return []
    return list(set(re.findall(r"\b\d+\s?mg\b", text.lower())))

def map_fda_to_serializer_data(fda_item, medication_type_id):
    #print (fda_item)
    openfda = fda_item.get("openfda", {})
    #print(openfda)
    name = ( get_first(openfda, "generic_name") or get_first(openfda, "brand_name") ).title()
    generic_name = get_first(openfda, "generic_name").lower()
    description = get_first(fda_item, "purpose") or get_first(fda_item, "indications_and_usage")
    side_effects = get_first(fda_item, "warnings")
    contraindications = get_first(fda_item, "do_not_use")
    is_prescription = "OTC" not in get_first(openfda, "product_type")
    common_dosages = extract_dosages(get_first(fda_item, "dosage_and_administration"))
    print (name,generic_name,get_first(openfda, "brand_name"),get_first(fda_item, "purpose"))
    return {
        "name": name,
        "generic_name": generic_name,
        "medication_type": medication_type_id,
        "description": description,
        "side_effects": side_effects,
        "contraindications": contraindications,
        "is_prescription": is_prescription,
        "common_dosages": common_dosages,
        "is_active": True
    }


class MedicationTypeView(viewsets.ModelViewSet):

    serializer_class = MedicationTypeSerializer
    permission_classes= [IsAuthenticated]

    def get_queryset(self):
        return MedicationType.objects.filter(is_active=True)


class MedicationView(viewsets.ModelViewSet):
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(is_active=True)



    def _normalize(term: str) -> str:
        return term.lower().strip()

    def search_data_fda(self,term, limit=5):
        fda_url = "https://api.fda.gov/drug/label.json"

        term = term
        if len(term) < 3 :
            return None

        search_query = (
            f"openfda.generic_name:{term}* OR "
            f"openfda.brand_name:{term}* OR "
            f"active_ingredient:{term}*"
        )
        params = {
            "search": search_query,
            "limit": limit
        }


        try:
            response= requests.get(fda_url,params=params, timeout=5)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"OpenFDA request failed: {e}")
            return None




    @action(detail=False, methods=['get'])
    def search(self, request):
        print("search debug")
        query = request.query_params.get('q','')

        if not query:
            return Response({
                'status':'error',
                'message': 'Search query parameter "q" is required'
            },status=400)

        print("q is :",query)
        try:
            medications = Medication.objects.filter(
                Q(name__icontains=query) |
                Q(generic_name__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            ).order_by('name')

            print( "medications db is:", medications)
            if medications.exists():
                print("found in database %s",query)
                serializer = self.get_serializer(medications, many=True)
                return Response(serializer.data)
            else:
                print("Not found in database %s start exeptions",query)
                get_data_fda =self.search_data_fda(query)
                #print ("fda data is: ", get_data_fda)
                if not get_data_fda or "results" not in get_data_fda:
                    return Response({
                        "status": "error",
                        "message": f"No results found for '{query}'"
                    }, status=status.HTTP_404_NOT_FOUND)           


                fda_item = get_data_fda["results"][1]
                # Determine the MedicationType name from FDA data (fallback to "Unknown")
                pharm_classes = fda_item.get("openfda", {}).get("pharm_class_epc", [])
                med_type_name = pharm_classes[0] if pharm_classes else "Unknown"
                # Get or create the MedicationType
                medication_type, _ = MedicationType.objects.get_or_create(name=med_type_name)
                serializer_data = map_fda_to_serializer_data(fda_item, medication_type.id)
                serializer = MedicationSerializer(data=serializer_data)
                if serializer.is_valid():
                    medication = serializer.save()
                    return Response(MedicationSerializer(medication).data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            print("Not found in database %s start exeptions",query)
            return Response({
                "status": "error",
                "message": f"No results found for '{query}'"
            }, status=status.HTTP_404_NOT_FOUND)    




class UserMedicationView(viewsets.ModelViewSet):
    queryset = UserMedication.objects.all()
    serializer_class = UserMedicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserMedicationLogView(viewsets.ModelViewSet):
    serializer_class = MedicationLogSerializer
    permission_classes= [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = MedicationLog.objects.filter(user=user)
        user_med_id = self.request.query_params.get('user_medication')
        if user_med_id:
            queryset = queryset.filter(user_medication_id=user_med_id)

        return queryset

    def perform_create(self, serializer):
        # Automatically assign the logged-in user
        serializer.save(user=self.request.user)


class MedicationReminderView(viewsets.ModelViewSet):
    serializer_class = MedicationReminderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MedicationReminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)