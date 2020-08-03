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
                COMPOSE_PROJECT_NAME="${JOB_BASE_NAME}_au_sg_chanel"
            }

            stages {
                stage('Setup') {
                    when {
                        changeRequest()
                    }


                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/api-channel/") {

                            checkout scm

                            sh '''#!/bin/bash
                                echo Starting Shared DB
                                python3 pie.py api.build
                                python3 pie.py api.start
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/api-channel")  {
                            sh '''#!/bin/bash
                                python3 pie.py api.test
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
