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

        stage('Create ENV File') {
            steps {
                withCredentials([
                    string(credentialsId: 'DATABASE_URL', variable: 'DATABASE_URL'),
                    string(credentialsId: 'DATABASE_URL_SYNC', variable: 'DATABASE_URL_SYNC')
                ]) {
                    sh '''
                    echo "DATABASE_URL=$DATABASE_URL" > .env
                    echo "DATABASE_URL_SYNC=$DATABASE_URL_SYNC" >> .env
                    '''
                }
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
