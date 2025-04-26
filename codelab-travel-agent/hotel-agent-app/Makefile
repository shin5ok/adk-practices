
NAME ?= hotel-agent-app
GOOGLE_CLOUD_LOCATION := us-central1
AGENT_PATH := hotel-agent-app/


.PHONY: deploy
deploy:
	adk deploy cloud_run \
	--project=$(GOOGLE_CLOUD_PROJECT) \
	--region=$(GOOGLE_CLOUD_LOCATION) \
	--service_name=$(NAME)  \
	--app_name=$(NAME) \
	--with_ui \
	$(AGENT_PATH)

.PHONY: sa
sa:
	@echo "Make service accounts"

	gcloud iam service-accounts create $(NAME)
	# gcloud iam service-accounts create cloudbuild


.PHONY: sa-iam
sa-iam:
	@echo "Grant some authorizations to the service account for Cloud Run service"

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(NAME)@$(GOOGLE_CLOUD_PROJECT).iam.gserviceaccount.com \
	--role=roles/discoveryengine.editor

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(NAME)@$(GOOGLE_CLOUD_PROJECT).iam.gserviceaccount.com \
	--role=roles/storage.objectUser

.PHONY: iam-cloudbuild
CLOUDBUILD_SA:=$(shell gcloud builds get-default-service-account | grep gserviceaccount | cut -d / -f 4)
iam-cloudbuild:
	@echo "Grant some authorizations to the service account for Cloud Build"

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(CLOUDBUILD_SA) \
	--role=roles/artifactregistry.repoAdmin

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(CLOUDBUILD_SA) \
	--role=roles/cloudbuild.builds.builder

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(CLOUDBUILD_SA) \
	--role=roles/run.admin

	gcloud projects add-iam-policy-binding $(GOOGLE_CLOUD_PROJECT) \
	--member=serviceAccount:$(CLOUDBUILD_SA) \
	--role=roles/storage.admin
