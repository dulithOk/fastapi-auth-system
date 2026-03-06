pipeline {
    agent any

    environment {
        APP_NAME = "fastapi-auth"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main',
                url: 'https://github.com/dulithOk/fastapi-auth-system.git'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                docker-compose down || true
                docker-compose build
                '''
            }
        }

        stage('Start Containers') {
            steps {
                sh '''
                docker-compose up -d
                '''
            }
        }

        stage('Check Running Containers') {
            steps {
                sh '''
                docker ps
                '''
            }
        }

    }

    post {
        success {
            echo 'Deployment Successful'
        }

        failure {
            echo 'Deployment Failed'
        }
    }
}
