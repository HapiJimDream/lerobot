from huggingface_hub import login, upload_folder

# (optional) Login with your Hugging Face credentials
login()

# Push your dataset files
upload_folder(folder_path="/home/jim/.cache/huggingface/lerobot/jim1234321/pick_red_block0613_10_20260613_122119", repo_id="jim1234321/pickred", repo_type="dataset")
