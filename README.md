# Research Assistant
A light weight memory-augmented RAG application **Research Assistant** built with **FastAPI**, **Ollama**, **ChromaDB** and **Transformers**. Supports *Persistent Memory*, *Tooling* and *Docker Deployment*. **~800MB** final docker image size. 
# Running The App
**Make** configurations are available for running the app in **Docker**.
## Prerequisites
- **Docker** (Needed for using **Make** commands)
- **Make**
- **Ollama** (Optional)
- **Python 3** (Optional) 
- **LLM Module (.onnx)** (Needed to run using **LLAMA CPP**)

That's it. Build it and it can run **offline!**.
### Using Makefiles commands
- **run** - Initiate a *docker compose* to run the app based on ***LLM Module*** *.env* flag.
- **run-with-container** - This will install a separate container for **OLLAMA** and our app. They communicate internally. **Phi3** mini model is setup. *Entrypoint* scripts are setup and our app will wait for the *Ollama container* to be ready. 
[IMP] *After creation the *Ollama container* will consume **~2.5G**.
- **stop** - Remove *docker containers* and any *startup script**
- **clean** - Stop and remove docker *containers* and *images* including any *volume mounts* 
- **create** - Create a *docker image* *.tar* file for deployment.
##### [IMPORTANT]: If you are using the *"run"*  command,  you need to ensure that app container can access the *OLLAMA* URL. For linux systems, this can be done by creating *config.toml* and adding the following in *$HOME_DIR/.ollama/config.toml* #####
[server]
listen = "0.0.0.0:11434"
### Running direct (Self Hosting)
You can also host the application locally. The project source code contains *requirements.txt* containing dependencies needed by the project.
- Create a *virtual env*	
  python -m venv .venv && source ./.venv/bin/activate
 - Install dependencies
 pip install -r requirements.txt
 - Tests are available and written with **pytest**. Install dev dependencies to run tests. **> 80% Coverage!**. Code quality ensured with **mypy**, **ruff** and **black**
 pip install -r dev-requirements.txt
 - Run the main module
 python -m main **OR** python ./main.py (If you are on the *ROOT_DIR*)
 - System Logs are available in **/logs** folder.
##### To avoid any permissions issue, remove any */models* (models for llama cpp) or */chroma_db* (persistent vector storage) or /logs or /sample_data (has the documents to be searched) directories.

## Configurations

The project depends on user configurations. Use **.env** file to set configurations when running locally. 
**Makefile** commands internally use *docker compose* to setup containers. The environment variables can be set in 
***docker-compose.base.yaml***

#### Overview
 Important Configurations
- **LLM_BACKEND** - Responsible for switching backends!
- **LLAMA_CPP_MODEL_FILE** - A compatible LLM Model for **LLama CPP** if using this backend
- **OLLAMA_CLIENT_URL** - If the **OLLAMA** backend is hosted in non-default url, can directly use it via this flag

These flags are enough to switch backends and run the app.
There are other configurations (like deciding request timeout, context window etc). Check **.env.example** for available configs.