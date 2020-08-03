#!groovy

// Testing pipeline

pipeline {
    agent {
        label 'hamlet-latest'
    }
    options {
        timestamps ()
        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )
        disableConcurrentBuilds()
        durabilityHint('PERFORMANCE_OPTIMIZED')
        parallelsAlwaysFailFast()
        skipDefaultCheckout()
        quietPeriod 60
    }

    environment {
        DOCKER_BUILD_DIR = "${env.DOCKER_STAGE_DIR}/${BUILD_TAG}"
    }

    parameters {
        booleanParam(
            name: 'all_tests',
            defaultValue: false,
            description: 'Run tests for all components'
        )
    }

    stages {
        stage('Setup') {
            steps {
                dir("${env.DOCKER_BUILD_DIR}/test/api-channel/") {
                    script {
                        def repoSharedDb = checkout scm
                        env["GIT_COMMIT"] = repoSharedDb.GIT_COMMIT
                    }
                }
            }
        }

        stage('Testing') {

            when {
                anyOf {
                    changeRequest()
                    equals expected: true, actual: params.all_tests
                }
            }

            environment {
                COMPOSE_PROJECT_NAME="au_sg_api_channel_sg_endpoint"
            }

            stages {
                stage('Setup') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/api-channel/") {

                            echo "Starting API Channel"

                            sh '''#!/bin/bash

                                # Create external network
                                if [[ -z "$(docker network ls --filter name=igl_local_devnet --quiet)" ]]; then
                                    docker network create igl_local_devnet
                                fi

                                #Setup minio staging location


                                python pie.py -R
                                export COMPOSE_PROJECT_NAME=au_sg_api_channel_sg_endpoint

                                mkdir -p --mode=u+rwx,g+rwxs,o+rwx "${DOCKER_BUILD_DIR}/test/api-channel/docker/volumes/${COMPOSE_PROJECT_NAME}/var/minio-data/.minio.sys"
                                ls -la ${DOCKER_BUILD_DIR}/test/api-channel/docker/volumes/${COMPOSE_PROJECT_NAME}/var/minio-data/

                                python pie.py api.build
                                python pie.py api.start

                                export COMPOSE_PROJECT_NAME=au_sg_api_channel_au_endpoint

                                mkdir -p --mode=u+rwx,g+rwxs,o+rwx "${DOCKER_BUILD_DIR}/test/api-channel/docker/volumes/${COMPOSE_PROJECT_NAME}/var/minio-data/.minio.sys"

                                python pie.py api.build
		                        python pie.py api.start
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/api-channel/")  {
                            sh '''#!/bin/bash
                                python pie.py test.start
                                python pie.py test.send_message
                                python pie.py test.subscribe
                            '''
                        }
                    }

                    post {
                        always {
                            dir("${env.DOCKER_BUILD_DIR}/test/api-channel/") {
                                junit 'api/tests/*.xml'
                            }
                        }
                    }

                }
            }

            post {
                cleanup {
                    dir("${env.DOCKER_BUILD_DIR}/test/api-channel/") {
                        sh '''#!/bin/bash
                            python3 pie.py api.destroy
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                if ( env.BRANCH_NAME == 'master' ) {
                    build job: '../cotp-devnet/build-api-channel/master', parameters: [
                        string(name: 'branchref_apichannel', value: "${GIT_COMMIT}")
                    ]
                }
            }
        }

        cleanup {
            cleanWs()
        }
    }
}
