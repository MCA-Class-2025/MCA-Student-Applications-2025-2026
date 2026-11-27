
# Fish AI — Image-Based Fish Identification and Analysis System
# 1. Project Overview
The Fish AI project is an image-based fish identification and analysis system. The main system uses a Convolutional Neural Network (CNN) model to identify the fish species from an uploaded image.

After the fish species is predicted, the system combines the prediction with information retrieved from external APIs. This enrichment provides additional information about the identified fish, including its biological characteristics, nutritional values, environmental details and geographical information.

In addition to the main fish identification and information system, the project includes a separate fish and shrimp disease classification module. This module is intended to classify diseases from the relevant uploaded fish or shrimp image.

The project therefore brings together image-based deep learning, external information retrieval and disease image classification in one overall application.
# 2. Project Objectives
The main objectives of the Fish AI project are:
- Identify fish species from user-uploaded images using a CNN-based image classification model.
- Display the predicted fish species to the user.
- Enrich the prediction with additional biological information retrieved through external APIs.
- Present nutritional information about the identified fish.
- Provide environmental and geographical information associated with the identified species.
- Include a separate image-classification module for fish and shrimp disease identification.
- Bring fish identification and related information into an accessible, image-based system.
# 3. System Modules
The project is organized into the following major modules.
# 3.1 Fish Image Upload
This module allows the user to provide an image of a fish for identification.

Purpose:
- Accept an image uploaded by the user.
- Provide the input image to the fish identification system.
- Start the image-based prediction workflow.
Input: Fish image uploaded by the user.

Output: Image supplied to the CNN prediction module.
# 3.2 CNN-Based Fish Species Identification
The main identification system uses a Convolutional Neural Network (CNN) to classify the uploaded fish image.

CNNs are deep learning models commonly used for image analysis. They learn visual patterns and features from images and use those learned features to predict an image class.

Purpose:
- Process the uploaded fish image.
- Extract visual features through the trained CNN model.
- Predict the fish species represented in the image.
- Return the predicted species label to the application.
Input: Uploaded fish image.

Output: Predicted fish species.

The exact CNN architecture, training dataset, number of species classes and model evaluation results should be documented here once the implementation details are finalized.
# 3.3 External API-Based Information Enrichment
After the CNN predicts the fish species, the application uses the prediction to retrieve additional information through external APIs.

This module extends the result beyond a species name by combining the prediction with related information from external sources.

The information categories described for this project are:
Information category	Purpose
Biological information	Provides additional biological details about the identified fish
Nutritional information	Provides nutrition-related values and details
Environmental information	Provides available environmental details associated with the species
Geographical information	Provides geographical or occurrence-related information


Workflow:
1. The CNN model predicts the fish species.
2. The predicted species is used by the information-enrichment workflow.
3. The application requests relevant information from the configured external APIs.
4. Retrieved information is combined with the species prediction.
5. The application presents the identification result and available additional details.
The actual API providers, endpoint names, response fields and handling of unavailable API results should be specified according to the implemented integrations.
# 3.4 Fish and Shrimp Disease Classification
The project also includes a separate disease classification module for fish and shrimp.

This module is distinct from the main fish species identification workflow. Its purpose is to classify disease-related categories from an uploaded fish or shrimp image.

Purpose:
- Accept a relevant fish or shrimp image.
- Process the image using the disease classification component.
- Predict the disease class represented by the image.
- Display the classification result to the user.
Input: Fish or shrimp image.

Output: Predicted disease category.

The disease model architecture, supported disease classes, training dataset and evaluation metrics should be added from the actual implementation. The module's output should be treated as an image-model prediction, not as a confirmed veterinary diagnosis.
# 4. Overall System Workflow
The main fish identification workflow follows this sequence:
                 User
                  |
                  v
          Upload Fish Image
                  |
                  v
          CNN-Based Prediction
                  |
                  v
          Predicted Fish Species
                  |
                  v
       External API Information Retrieval
                  |
        +---------+----------+-----------+
        |         |          |           |
        v         v          v           v
     Biological Nutrition Environmental Geographical
    Information Information Information Information
        |         |          |           |
        +---------+----------+-----------+
                  |
                  v
       Combined Identification Result
                  |
                  v
          Display to the User
The separate disease classification workflow is:
                 User
                  |
                  v
       Upload Fish or Shrimp Image
                  |
                  v
        Disease Classification Model
                  |
                  v
       Predicted Disease Category
                  |
                  v
          Display Result to User
These diagrams describe the functional workflows at a high level. They do not imply a specific CNN architecture, API provider or software deployment design.
# 5. Main Features
- Image-based fish identification: predicts a fish species from an uploaded image.
- CNN-based classification: uses a deep learning model for visual recognition.
- Biological information enrichment: adds biological details to the species prediction through external APIs.
- Nutritional information: provides nutrition-related information for the identified species.
- Environmental information: presents available environmental details.
- Geographical information: adds available geographical or occurrence-related details.
- Separate disease classification: includes a module for fish and shrimp disease image classification.
- Combined result presentation: brings the species prediction and retrieved information together for the user.
# 6. Technologies and Components
The project overview confirms the use of the following technical components:
Component	Role in the project
Convolutional Neural Network (CNN)	Main fish species image classification
Deep learning / image classification	Visual feature learning and image prediction
External APIs	Retrieval of biological, nutritional, environmental and geographical information
Disease classification model	Separate fish and shrimp disease image classification

<img width="1063" height="711" alt="image" src="https://github.com/user-attachments/assets/d95a709d-43b8-43f1-99e4-95c33ad4396c" />

<img width="1062" height="630" alt="image" src="https://github.com/user-attachments/assets/b7308e26-e2fc-40bc-8c0e-32b75866be74" />

<img width="1065" height="319" alt="image" src="https://github.com/user-attachments/assets/b48a48dc-1655-453a-8628-baead69f7225" />

<img width="1053" height="367" alt="image" src="https://github.com/user-attachments/assets/bbd3a582-1a28-4efb-863b-bab11554a054" />

<img width="1063" height="438" alt="image" src="https://github.com/user-attachments/assets/c40f18af-323b-427a-a3c8-21096a233a1e" />


