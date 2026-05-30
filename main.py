from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field,computed_field
from typing import Annotated,Literal,Optional
#typing import Annotated for addding validation description
import json
#Path, function is useded to provide metadata validation,rules and documentaton
#HTTPException for showing error if any type of error occur from client or dserver side 
app  = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City where the patient lives")]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient")]
    gender: Annotated[Literal["male", "female", "others"], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in meters")]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kg")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "underweight"
        elif self.bmi < 25:
            return "normal"
        elif self.bmi < 30:
            return "overweight"
        else:
            return "obese"


class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]   # FIX: must be int not str
    gender: Annotated[Optional[Literal["male", "female", "others"]], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]   # FIX: Optional not lowercase optional
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


def load_data():
    with open('patient.json','r') as f:
        data = json.load(f)

    return data 

# function in which u give dict that will put data  into  the json file 
def save_data(data):
    with open("patient.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.get("/")
def hello():
    return { 'message ': 'patient management system '}

@app.get("/about")   # FIX: cannot have two @app.get("/") endpoints, changed second one to /about
def about():
    return{'message':'A fully functional API to manges your patient'}

@app.get("/view")
def view():

    data = load_data()
    return data 

@app.get('/patient/{patient_id}') # ID of the patient in the DB' this give description just above the serach box 
def view_patient(patient_id: str = Path(..., description = 'ID of the patient in the DB', example = 'P001')):
    #load all the patient #..., is given  for saying parameter  is required 
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='patient not found')


#query() is a utility function provided by the fastapi 
#to decleare ,valdiate and document querry parameter in fastapi endpoints

@app.get('/sort')
def sort_patient(sort_by: str = Query(..., description = 'sort on the basis of height, weight or  bmi '),
                 order: str = Query('asc',description = 'sort in asc desc order ')):
    
    valid_feilds = ['height','weight','bmi']

    if sort_by not in valid_feilds:
        raise HTTPException(status_code=400, detail =f'invalid field select from {valid_feilds}')
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400, detail ='invalid order select between asc and desc ')
    data = load_data()
    
    sort_order = True if order == 'desc' else False

    sorted_data = sorted(data.values(), key = lambda x:x.get(sort_by,0), reverse=sort_order)

    return sorted_data                
    
@app.post('/create')
def create_patient(patient:Patient): # here patient we are getting pydantivc object 
    #loaad existing patient 
    data = load_data()

    #check if the patient already exist
    if patient.id in data:
        raise HTTPException(status_code=400, detail='patient already exist')
    
    #now patient add to the database 
    data[patient.id] = patient.model_dump(exclude=['id'])
    #model_dump use for convertint pydantic object into dictionary 
    #patient.id it it the key for rest all data 

    save_data(data)
    #save data in the form of json file

    return JSONResponse(status_code=201, content = {'message':'patient created'})


@app.put('/edit/{patient_id}')
def update_patient(patient_id:str, patient_update:PatientUpdate):
    
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail = 'patient not foound ')
    
    existing_patient_info = data[patient_id]
    #we havee bring existing patient bcz we wil change in it 


    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    #while concverting json into dict (using model. dumnmp) all the item in the patient info chnageg
    #if some itme is not chnaged then also it vlue cames as none from above so we put unset = true so that we get the value that is to be changed for eg city and name 
    # now the dictionary will be amd containing 2 value only new city and name 
    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value #loop is running on updated_patient_info changes is made in existing_patient_info
       
    #existing_patient_info-pydantic object -> update bmi + verdict  -> pydantic object 
    # we have to do above step bcz by changing wt bmi will also be changed so we need to update bmi also ans we dont have simple mechanism to do so 
    #thatswhy we have to go by above process  
   #existing_patient_info-pydantic object ->
    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)

    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')
   
    # add this dictionary to data 
    data[patient_id] = existing_patient_info
   
    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient updated'})


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    #load data 
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail = 'patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse( status_code=200, content = {'message':'patient deelted '})
