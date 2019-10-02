#!/usr/bin/env bash

BUILD_DIR=./target

mkdir -p ${BUILD_DIR}/profile
cp -r ./src/nuvo_polyglot/*.py ${BUILD_DIR}
cp -r ./polyglot/profile ${BUILD_DIR}/
cp -r ./polyglot/install.sh ${BUILD_DIR}
cp -r ./polyglot/server.json ${BUILD_DIR}

cd ${BUILD_DIR}/profile
zip -r ../profile.zip *
