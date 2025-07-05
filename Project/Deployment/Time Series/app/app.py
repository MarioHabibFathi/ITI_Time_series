import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from io import StringIO
import base64

# ----- CONFIGURATION -----
FASTAPI_URL = "http://localhost:8000"  # Adjust when deployed with Docker

st.set_page_config(page_title="📊 Time Series Forecasting", layout="wide")

st.title("📈 Time Series Forecasting Dashboard")

modal_component = components.declare_component("modal_component", url="http://localhost:5173")
#modal_component = components.declare_component("modal_component", path="frontend/modal_component/dist",)

# ----- FETCH MODELS & DATASETS FROM FASTAPI -----
# @st.cache_data(show_spinner=False)
# def fetch_models():
#     try:
#         resp = requests.get(f"{FASTAPI_URL}/models")
#         return resp.json().get("models", [])
#     except:
#         return []

# @st.cache_data(show_spinner=False)
# def fetch_datasets():
#     try:
#         resp = requests.get(f"{FASTAPI_URL}/datasets")
#         return resp.json().get("datasets", [])
#     except:
#         return []



@st.cache_data(show_spinner=False)
def fetch_models():
    return ["Model_A.pkl", "Model_B.pkl", "Mock_Model_C.pkl"]

@st.cache_data(show_spinner=False)
def fetch_datasets():
    return ["dataset1.csv", "dataset2.csv", "dummy_dataset.csv"]



def handle_filename_conflict(initial_name, upload_file=None, is_rename=False, old_filename=None):
    """
    Handles file conflict resolution for uploads or renames.
    - initial_name: The filename user provided.
    - upload_file: If not None → UploadFile object for upload; if None → for renaming.
    - is_rename: True if this is a rename operation.
    - old_filename: Required if is_rename=True; the current file being renamed.
    """

    # First, check if the filename already exists
    check_resp = requests.post(
        f"{FASTAPI_URL}/upload/check_file", 
        data={"filename": initial_name}
    )
    check_data = check_resp.json()

    if not check_data["exists"]:
        if is_rename:
            return rename_file(old_filename, initial_name)
        else:
            return upload_file_to_server(upload_file, initial_name)

    st.warning(f"⚠️ File `{initial_name}` already exists.")

    option = st.radio("Choose action:", ["Rename", "Increment", "Overwrite", "Cancel"], key=f"conflict_{initial_name}")

    if option == "Rename":
        new_name = st.text_input("Enter new filename:", key=f"rename_{initial_name}")
        if st.button("Save with New Name", key=f"rename_btn_{initial_name}"):
            if new_name == initial_name:
                st.error("❗ New filename is the same as the existing filename. Choose another.")
                return
            return handle_filename_conflict(new_name, upload_file=upload_file, is_rename=is_rename, old_filename=old_filename)

    elif option == "Increment":
        inc_resp = requests.post(
            f"{FASTAPI_URL}/upload/increment_name", 
            data={"filename": initial_name}
        ).json()
        incremented_name = inc_resp["new_name"]

        if is_rename:
            return rename_file(old_filename, incremented_name)
        else:
            return upload_file_to_server(upload_file, incremented_name)

    elif option == "Overwrite":
        if is_rename:
            st.error("❗ Overwrite option is not supported for renaming. Choose Rename, Increment, or Cancel.")
            return
        return upload_file_to_server(upload_file, initial_name, mode="overwrite")

    else:
        st.info("Operation canceled.")
        return


def upload_file_to_server(upload_file, filename, mode="error"):
    with st.spinner("Uploading file..."):
        save_resp = requests.post(
            f"{FASTAPI_URL}/upload/save_file",
            files={"file": (upload_file.name, upload_file)},
            data={"filename": filename, "mode": mode}
        )
        if save_resp.ok:
            st.success(f"✅ File uploaded as `{filename}`")
        else:
            st.error(f"❌ Upload failed: {save_resp.text}")


def rename_file(old_name, new_name):
    with st.spinner("Renaming file..."):
        resp = requests.post(
            f"{FASTAPI_URL}/datasets/rename",
            data={"old_filename": old_name, "new_filename": new_name}
        )
        if resp.ok:
            st.success(f"✅ Renamed `{old_name}` → `{new_name}`")
        else:
            st.error(f"❌ Rename failed: {resp.text}")



models = fetch_models()
datasets = fetch_datasets()

# ----- SIDEBAR CONFIGURATION -----
with st.sidebar:
    st.header("⚙️ Configuration")
    selected_model = st.selectbox("Select Model", models or ["No models found"])
    selected_dataset = st.selectbox("Select Dataset", datasets or ["No datasets found"])

# ----- TABS -----
tab0, tab1, tab2, tab3 = st.tabs(["📈 EDA", "🛠 Train Model", "🔮 Predict & Visualize", "📊 Metrics"])

# ----- TAB 0: EDA -----
with tab0:
    st.subheader("Exploratory Data Analysis (EDA)")
    
    colA, colB = st.columns([1, 2])
    
    with colA:
        if selected_dataset:
            if st.button(f"📂 Load Dataset `{selected_dataset}`"):
                with st.spinner(f"Loading dataset `{selected_dataset}`..."):
                    try:
                        response = requests.get(f"{FASTAPI_URL}/dataset/{selected_dataset}", timeout=30)
                        if response.ok:
                            csv_data = response.text
                            df = pd.read_csv(StringIO(csv_data))
                            st.success(f"Dataset `{selected_dataset}` loaded successfully.")
                            st.write("### Preview of Dataset")
                            st.dataframe(df.head())

                            st.write("### Summary Statistics")
                            st.dataframe(df.describe())

                            if "date" in df.columns:
                                df['date'] = pd.to_datetime(df['date'])
                                df = df.sort_values("date")

                                numeric_cols = df.select_dtypes(include=['int', 'float']).columns.tolist()
                                if numeric_cols:
                                    value_col = st.selectbox("Select numeric column to plot:", numeric_cols)
                                    st.line_chart(df.set_index("date")[value_col])
                                else:
                                    st.warning("No numeric columns found to plot against 'date'.")
                            else:
                                st.warning("Expected column 'date' not found in dataset.")

                            # if "date" in df.columns and "value" in df.columns:
                            #     df['date'] = pd.to_datetime(df['date'])
                            #     df = df.sort_values("date")
                            #     st.line_chart(df.set_index("date")["value"])
                            # else:
                            #     st.warning("Expected columns 'date' and 'value' not found in dataset.")
                        else:
                            st.error(f"Failed to load dataset: {response.text}")
                    except Exception as e:
                        st.error(f"Error fetching dataset: {e}")
                        
            
            st.markdown("#### ⚠️ Dataset Actions")
            subcol1, subcol2 = st.columns([1, 1])
            
            with subcol1:
                # if st.button(f"🗑️ Delete Dataset: `{selected_dataset}`"):
                #     with st.spinner("Deleting dataset..."):
                #         resp = requests.delete(f"{FASTAPI_URL}/dataset/delete", data={"filename": selected_dataset})
                #         if resp.ok:
                #             st.success(f"Dataset `{selected_dataset}` deleted successfully.")
                #         else:
                #             st.error(f"Failed to delete dataset: {resp.text}")


                if st.button(f"🗑️ Delete Dataset: `{selected_dataset}`"):
                    st.session_state.show_delete_modal = True  
                    
                if st.session_state.get("show_delete_modal", False):
                    confirm_delete = modal_component(
                        label="Confirm Delete",
                        message=f"Are you sure you want to delete `{selected_dataset}`?",
                        buttons=["Yes", "No"],
                        key=f"delete_modal_{selected_dataset}"
                    )
            
                    if confirm_delete == "Yes":
                        with st.spinner("Deleting dataset..."):
                            resp = requests.delete(
                                f"{FASTAPI_URL}/datasets/delete",
                                data={"filename": selected_dataset}
                            )
                            if resp.ok:
                                st.success(f"✅ Dataset `{selected_dataset}` deleted successfully.")
                            else:
                                st.error(f"❌ Failed to delete dataset: {resp.text}")
                        st.session_state.show_delete_modal = False  # hide modal after action
            
                    elif confirm_delete == "No":
                        st.info("❎ Deletion canceled.")
                        st.session_state.show_delete_modal = False
            # st.markdown("---")  

            with subcol2:
                if st.button(f"✏️ Rename Dataset: `{selected_dataset}`"):
                    st.session_state.show_rename_input = True
                    rename_placeholder = st.empty()
                    
                    if st.session_state.show_rename_input:
                        with rename_placeholder.container():

                            new_name = st.text_input("Enter New Dataset Name:")
                            confirm = st.button("✅ Confirm Rename")
                            cancel = st.button("❌ Cancel")
                
                            if confirm:
                                with st.spinner("Renaming dataset..."):
                                    resp = requests.post(
                                        f"{FASTAPI_URL}/dataset/rename",
                                        json={"old_name": selected_dataset, "new_name": new_name}
                                    )
                                    if resp.ok:
                                        st.success(f"Renamed to `{new_name}`")
                                        st.session_state.show_rename_input = False
                                        rename_placeholder.empty()
                                    else:
                                        st.error(f"Failed to rename dataset: {resp.text}")

                    if cancel:
                        st.session_state.show_rename_input = False
                        rename_placeholder.empty()
                # st.markdown("#### ✏️ Rename Dataset")
                # new_name = st.text_input("New name for dataset", value=selected_dataset)
                # if st.button(f"Rename Dataset: `{selected_dataset}`"):
                #     with st.spinner("Renaming dataset..."):
                #         resp = requests.post(
                #             f"{FASTAPI_URL}/dataset/rename",
                #             json={"old_name": selected_dataset, "new_name": new_name}
                #         )
                #         if resp.ok:
                #             st.success(f"Renamed to `{new_name}`")
                #         else:
                #             st.error(f"Failed to rename dataset: {resp.text}")

            # st.markdown("---")

    with colB:
        
        subcol1, subcol2 = st.columns([1, 1])  # Inner split

        with subcol1:
            st.markdown("**Or upload your own dataset:**")

        # st.markdown("<small>### Or upload your own dataset:</small>", unsafe_allow_html=True)
        
        
        with subcol2:
            uploaded_file = st.file_uploader("Choose a CSV or TSV file", type=["csv", "tsv"],label_visibility="collapsed")
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
            # ----- Dataset Save Controls -----
            st.markdown("#### 💾 Save Dataset")
            save_name = st.text_input("File Name to Save", file_name)
            save_mode = st.selectbox("Save Mode", ["error", "overwrite", "increment"])
            if st.button("Save Dataset to Server"):
                with st.spinner("Saving dataset..."):
                    resp = requests.post(
                        f"{FASTAPI_URL}/upload/save_file",
                        data={"filename": save_name, "mode": save_mode},
                        files={"file": file_bytes}      
                    )
                    if resp.ok:
                        st.success(f"File saved as: `{save_name}`")
                    else:
                        st.error(f"Error saving file: {resp.text}")



            if st.button("🔎 Inspect Uploaded Dataset"):
                with st.spinner("Analyzing uploaded dataset..."):
                    resp = requests.post(f"{FASTAPI_URL}/eda/schema", files={"file": file_bytes})
                    if resp.ok:
                        schema = resp.json()

                        st.write("### Schema Overview")
                        st.json(schema)

                        if st.checkbox("Show Null Values Table"):
                            null_table = pd.DataFrame.from_dict(schema['nulls'], orient='index', columns=['Null Count'])
                            st.dataframe(null_table)

                        st.write("### Column Type Suggestions (Optional)")
                        if st.button("Suggest Types for Columns"):
                            suggest_resp = requests.post(f"{FASTAPI_URL}/eda/suggest-types", files={"file": file_bytes})
                            if suggest_resp.ok:
                                st.json(suggest_resp.json())
                            else:
                                st.error("Failed to fetch type suggestions.")
                    else:
                        st.error(f"Error analyzing file: {resp.text}")

            st.markdown("---")
            st.write("## ⚙️ Data Cleaning Actions")

            selected_column = st.text_input("Column to Cast, Drop, or Analyze")

            col1, col2 = st.columns(2)

            with col1:
                new_dtype = st.selectbox("Type to Cast", ["int64", "float64", "datetime64[ns]", "object", "category"])
                if st.button("Attempt Type Cast"):
                    resp = requests.post(
                        f"{FASTAPI_URL}/eda/try-cast-column",
                        files={"file": file_bytes},
                        data={"column": selected_column, "dtype": new_dtype}
                    )
                    if resp.ok:
                        result = resp.json()
                        st.json(result)
                        if not result.get("success") and result.get("non_convertible_rows", 0) > 0:
                            if st.button("Drop Non-Convertible Rows"):
                                drop_resp = requests.post(
                                    f"{FASTAPI_URL}/eda/drop-non-convertible-rows",
                                    files={"file": file_bytes},
                                    data={"column": selected_column, "dtype": new_dtype}
                                )
                                st.json(drop_resp.json())
                    else:
                        st.error("Type casting failed.")

            with col2:
                if st.button("Drop Column"):
                    resp = requests.post(
                        f"{FASTAPI_URL}/eda/drop-column",
                        files={"file": file_bytes},
                        data={"column": selected_column}
                    )
                    if resp.ok:
                        st.json(resp.json())
                    else:
                        st.error("Failed to drop column.")

                if st.button("Drop Rows with Null in Column"):
                    resp = requests.post(
                        f"{FASTAPI_URL}/eda/drop-rows-with-null",
                        files={"file": file_bytes},
                        data={"column": selected_column}
                    )
                    if resp.ok:
                        st.json(resp.json())
                    else:
                        st.error("Failed to drop rows.")

            st.markdown("---")
            st.write("### 📥 Download Cleaned Dataset")
            if st.button("Download Cleaned File"):
                resp = requests.post(f"{FASTAPI_URL}/eda/save-cleaned", files={"file": file_bytes})
                if resp.ok:
                    b64 = base64.b64encode(resp.content).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="cleaned_{uploaded_file.name}">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.error("Could not generate download file.")


# ----- TAB 1: Train Model -----
with tab1:
    st.subheader("Train a New Model on Selected Dataset")

    if st.button("Start Training"):
        with st.spinner("Training in progress..."):
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/train",
                    json={"model_name": selected_model, "dataset_name": selected_dataset},
                    timeout=300  # You can adjust depending on training time
                )
                if response.ok:
                    st.success(response.json().get("message", "Training completed successfully."))
                else:
                    st.error(f"Training failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# ----- TAB 2: Predict & Visualize -----
with tab2:
    st.subheader("Run Forecast & Visualize Results")

    if st.button("Run Prediction"):
        with st.spinner("Running prediction..."):
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/predict",
                    json={"model_name": selected_model, "dataset_name": selected_dataset},
                    timeout=120
                )
                if response.ok:
                    data = response.json()
                    predictions = data.get("predictions", [])

                    if predictions:
                        df = pd.DataFrame(predictions, columns=["Forecast"])
                        st.success("Prediction completed successfully!")
                        st.line_chart(df)
                        st.dataframe(df)
                    else:
                        st.warning("No predictions returned.")

                else:
                    st.error(f"Prediction failed: {response.text}")

            except Exception as e:
                st.error(f"Error: {e}")

# ----- TAB 3: Metrics -----
with tab3:
    st.subheader("Service & Model Metrics")

    if st.button("Refresh Metrics"):
        try:
            response = requests.get(f"{FASTAPI_URL}/metrics")
            if response.ok:
                st.code(response.text, language="yaml")
            else:
                st.error("Could not fetch metrics.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.info("More detailed visualizations and real-time monitoring will be added soon.")
