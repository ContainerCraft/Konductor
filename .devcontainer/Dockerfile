# Description: This file is used to build the devcontainer at runtime.
# Add additional dependencies below the `FROM` line as needed.

FROM ghcr.io/containercraft/devcontainer:latest

# Install additional dependencies by extending the base image
#ARG DEBIAN_FRONTEND=noninteractive
#ARG APT_PACKAGES="\
#"
#
#RUN set -ex \
#    && apt-get update \
#    && apt-get install -y $APT_PACKAGES \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/* \
#    && echo

##################################################################################
# Install AWS CLI v2

USER root
RUN echo \
    && ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "x86_64"; else if ($1 == "aarch64" || $1 == "arm64") print "aarch64"; else print "unknown" }') \
    && NAME="aws" \
    && PKG="awscli-exe-linux-${ARCH}.zip" \
    && URL="https://awscli.amazonaws.com/${PKG}" \
    && DIR="/tmp/awscli" \
    && echo "---------------------------------------------------------"\
    && echo "INFO[${NAME}] Installed:" \
    && echo "INFO[${NAME}]   Command:        ${NAME}" \
    && echo "INFO[${NAME}]   Package:        ${PKG}" \
    && echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
    && echo "INFO[${NAME}]   Source:         ${URL}" \
    && echo "---------------------------------------------------------"\
    && mkdir -p ${DIR} \
    && curl -L ${URL} --output ${DIR}/${PKG} \
    && unzip ${DIR}/${PKG} -d ${DIR} \
    && bash ${DIR}/aws/install \
    && rm -rf ${DIR} \
    && aws --version \
    && echo
USER vscode

###################################################################################
## Install Google Cloud SDK
#
#ENV CLOUDSDK_INSTALL_DIR /usr/local/gcloud/
#ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin
#
#USER root
#RUN echo \
#    && export ARCH=$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }') \
#    && export NAME="gcloud" \
#    && export TEST="${NAME} version" \
#    && export PKG="google-cloud-sdk.tar.gz" \
#    && export URL="https://dl.google.com/dl/cloudsdk/release/${PKG}" \
#    && export DIR="/usr/local/gcloud" \
#    && echo "---------------------------------------------------------"\
#    && echo "INFO[${NAME}] Installed:" \
#    && echo "INFO[${NAME}]   Command:        ${NAME}" \
#    && echo "INFO[${NAME}]   Package:        ${PKG}" \
#    && echo "INFO[${NAME}]   Architecture:   ${ARCH}" \
#    && echo "INFO[${NAME}]   Source:         ${URL}" \
#    && echo "---------------------------------------------------------"\
#    && mkdir -p ${DIR} \
#    && ${curl} ${URL} | tar xzvf - --directory ${DIR} \
#    && /usr/local/gcloud/google-cloud-sdk/install.sh -q \
#    && ${dir_clean} \
#    && ${TEST} \
#    && echo
#USER vscode
