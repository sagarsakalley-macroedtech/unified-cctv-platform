Project Description

The Unified CCTV Control Room is a centralized CCTV monitoring and management platform designed to provide a single interface for monitoring camera systems from multiple departments and locations. The platform includes a structured camera registry containing camera identification, department, district, location, camera type, and operational information. It provides filtering and search capabilities that allow control-room operators to quickly identify and access cameras based on city, status, camera code, or other available parameters.

The platform also includes an AI-based Camera Health Prediction module using a Random Forest machine-learning model. The system evaluates important camera-performance parameters such as uptime, response time, packet loss, and CPU usage to estimate camera health and generate a health score. This module is designed to help operators identify potentially unhealthy cameras and support proactive monitoring and maintenance.

An OpenCV-based CCTV Video Viewer is integrated into the platform for video processing and demonstration. The system can work with CCTV video sources and sample media such as cctv_demo.mp4, providing a foundation for future real-time video analytics, object detection, motion detection, and other computer-vision capabilities. The application is developed using Python, Streamlit, OpenCV, Pandas, Scikit-learn, FastAPI, PostgreSQL, SQLAlchemy, and Docker, providing a modular architecture that can be extended for larger-scale deployment.

The project is also containerized using Docker and maintained through GitHub, making the application easier to reproduce, deploy, and maintain. The current implementation demonstrates centralized CCTV registry management, camera health monitoring, AI-based prediction, video processing, database integration, and an interactive control-room dashboard.

Live demo : https://unified-cctv-platform.streamlit.app/
