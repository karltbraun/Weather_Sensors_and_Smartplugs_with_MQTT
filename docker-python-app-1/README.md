# docker-python-app/README.md

# Docker Python App

This project contains two main application scripts for processing sensor data and integrating with Shelly devices, packaged within a Docker container.

## Project Structure

```
docker-python-app
├── src
│   ├── republish_processed_sensors_main.py
│   ├── shelly_main.py
│   └── modules/
│       └── shared_modules/
├── Dockerfile
├── requirements.txt
├── .dockerignore
└── README.md
```

## Getting Started

To build and run the Docker container for this application, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd docker-python-app
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t docker-python-app .
   ```

3. **Run the Docker container:**
   ```bash
   docker run --rm docker-python-app
   ```

## Dependencies

The required Python libraries are listed in the `requirements.txt` file. Make sure to review and update this file as necessary.

## Dockerfile

The `Dockerfile` contains the instructions to build the Docker image, including the base image, copying application files, and installing dependencies.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.