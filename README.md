# Open Cycling Framework
## Requirements  
- Python 3 (tested on 3.8.7)  
- pip requirements from requirements.txt
- open [dataset](https://academictorrents.com/details/bf76b193960a96a683f9c2afde70acab9d3d757d)
## Installation  
The whole pip requirements could be installed with  
```
pip install -r requirements.txt
```
## Dataset
When the dataset is loaded please copy folder Sport5 to the folder 'data'. Otherwise please specify the location in config.py.
## Pipeline
### 1. Calculate FTP of the riders  
First of all, it is necessary to calculate FTP (functional threshold power). You could do that with  
```
python calculate_ftp.py
```  
**This step could be skipped since the FTP values for the default dataset are already available in the metadata directory**  
### 2. Processing of the .tcx files  
The framework should preprocess the raw .tcx files into the aggregated .csv table. Please use  
``` 
python data_preprocessing.py
```
to prepare this table.  
### 3. Prediction model  
All the analytical code is delivered in a jupyter notebook ```data_overview.ipynb```
  
