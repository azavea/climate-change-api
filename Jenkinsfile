#!groovy

node {
  try {
    // Checkout the proper revision into the workspace.
    stage('checkout') {
      checkout scm
    }

    env.AWS_PROFILE = 'climate'
    env.CC_DOCS_FILES_BUCKET = 'staging-us-east-1-climate-docs'
    env.GIT_COMMIT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()

    // Execute `cibuild` wrapped within a plugin that translates
    // ANSI color codes to something that renders inside the Jenkins
    // console.
    stage('cibuild') {
      wrap([$class: 'AnsiColorBuildWrapper']) {
        sh 'scripts/cibuild'
        step([$class: 'WarningsPublisher',
          parserConfigurations: [[
            parserName: 'Pep8',
            pattern: 'django/climate_change_api/violations.txt'
          ]],
          // mark build unstable if there are any linter warnings
          unstableTotalAll: '0',
          usePreviousBuildAsReference: true
        ])
      }
    }

    if (env.BRANCH_NAME == 'develop' || env.BRANCH_NAME.startsWith('release/')) {
      env.AWS_DEFAULT_REGION = 'us-east-1'
      env.CC_SETTINGS_BUCKET = 'staging-us-east-1-climate-config'
      env.CC_S3STORAGE_BUCKET = 'climate-change-api-staging'
      env.GIT_COMMIT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()

      if (env.BRANCH_NAME.startsWith('release/')) {
        // Deploy release branches into production
        env.CC_SETTINGS_BUCKET = 'production-climate-config-us-east-1'
        env.CC_S3STORAGE_BUCKET = 'climate-change-api-production'
      }

      // Publish container images built and tested during `cibuild`
      // to the private Amazon Container Registry tagged with the
      // first seven characters of the revision SHA.
      stage('cipublish') {
        // Decode the `AWS_ECR_ENDPOINT` credential stored within
        // Jenkins. In includes the Amazon ECR registry endpoint.
        withCredentials([[$class: 'StringBinding',
                          credentialsId: 'CC_AWS_ECR_ENDPOINT',
                          variable: 'CC_AWS_ECR_ENDPOINT']]) {
          wrap([$class: 'AnsiColorBuildWrapper']) {
            sh './scripts/cipublish'
          }
        }
      }

      // Plan and apply the current state of the instracture as
      //
      // Also, use the container image revision referenced above to
      // cycle in the newest version of the application into Amazon
      // ECS.
      stage('infra') {
        // Use `git` to get the primary repository's current commmit SHA and
        // set it as the value of the `GIT_COMMIT` environment variable.
        wrap([$class: 'AnsiColorBuildWrapper']) {
          sh './scripts/infra plan'
          sh './scripts/infra apply'
        }
      }
    }
  } catch (err) {
    // Some exception was raised in the `try` block above. Assemble
    // an appropirate error message for Slack.
    def slackMessage = ":jenkins-angry: *doe-climate-change (${env.BRANCH_NAME}) #${env.BUILD_NUMBER}*"
    if (env.CHANGE_TITLE) {
      slackMessage += "\n${env.CHANGE_TITLE} - ${env.CHANGE_AUTHOR}"
    }
    slackMessage += "\n<${env.BUILD_URL}|View Build>"
    slackSend  channel: '#doe-climate-change', color: 'danger', message: slackMessage

    // Re-raise the exception so that the failure is propagated to
    // Jenkins.
    throw err
  } finally {
    // Pass or fail, ensure that the services and networks
    // created by Docker Compose are torn down.
    sh 'docker-compose down -v'
  }
}
