# InformatIQ💡


## Welcome to InformatIQ. A place where information is made simple.

💡Upload a PDF to the InformaIQ web-app. It will extract the important information for you which can be downloaded as a CSV.

### Step 1: Download Repository
Download the repository from GitHub to your local machine.

### Step 2: Download the Model
Use the link given below to access the  `'bert-base-multilingual-cased-v4'` fine-tuned model. Place the model folder in the web_app folder on your local machine.

Make sure the the name of the folder is `model` and it is placed inside the `web_app` folder.

Note: Both the distilbert and bert fine-tuned versions are available on HuggingFace Hub at the following links:

`distilbert-base-multilingual-cased-v6`: https://huggingface.co/sumeet-hande/distilbert-base-multilingual-cased-v6

`bert-base-multilingual-cased-v4`: https://huggingface.co/sumeet-hande/bert-base-multilingual-cased-v4

### Step 3: Download Dependencies
Use the `requirements.txt` file in the web_app folder to download all required dependencies to run the streamlit web-app.

### Step 4: Run the streamlit web-app
`app_router.py` is the entrypoint of the web-app. Use the following command to start the web-app.

`streamlit run app_router.py`

The following snapshot gives a glimpse of the streamlit web-app "InformatIQ"'s homepage.


![image](https://github.com/user-attachments/assets/eefa079d-8539-4c0d-8008-58a25480d31f)
