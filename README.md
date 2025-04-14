# Running the Project with Docker

This section provides instructions to build and run the project using Docker.

## Prerequisites

- Ensure Docker and Docker Compose are installed on your system.
- The project requires Python 3.11 as specified in the Dockerfile.

## Environment Variables

- Define the following environment variables in a `.env` file or directly in the Docker Compose file:
  - `POSTGRES_USER`: Database username (default: `user`)
  - `POSTGRES_PASSWORD`: Database password (default: `password`)

## Build and Run Instructions

1. Build the Docker images and start the services:

   ```bash
   docker-compose up --build
   ```

2. Access the application:
   - Application: [http://localhost:8501](http://localhost:8501)
   - Database: Port `1234`
   - Neo4j: Port `7687`

## Notes

- The application source code and dependencies are managed within the Docker container.
- The database service uses a persistent volume `db_data` to store data.

For further details, refer to the project documentation.