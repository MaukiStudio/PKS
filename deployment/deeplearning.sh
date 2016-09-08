# Step 0 : deploy.sh

# Step 1 : Device Driver
# Graphics Driver 를 nvidia 것으로 바꾼다.
#   시스템설정 > 소프트웨어&업데이트 > 추가드라이버

# Step 2 : CUDA
wget http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers/cuda_7.5.18_linux.run
chmod +x cuda_7.5.18_linux.run
sudo ./cuda_7.5.18_linux.run --override
# Do you accept the previously read EULA? (accept/decline/quit): accept
# You are attempting to install on an unsupported configuration. Do you wish to continue? ((y)es/(n)o) [ default is no ]: yes
# Install NVIDIA Accelerated Graphics Driver for Linux-x86_64 352.39? ((y)es/(n)o/(q)uit): no
# Install the CUDA 7.5 Toolkit? ((y)es/(n)o/(q)uit): yes 
# Enter Toolkit Location [ default is /usr/local/cuda-7.5 ]: 그냥 엔터
# Do you want to install a symbolic link at /usr/local/cuda? ((y)es/(n)o/(q)uit): yes
# Install the CUDA 7.5 Samples? ((y)es/(n)o/(q)uit): no
echo "export PATH=/usr/local/cuda/bin:$PATH" >> ~/.bashrc
echo "LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH" >> ~/.bashrc

# Step 3 : CUDNN
# https://developer.nvidia.com/rdp/cudnn-download 에 접속
# 로그인 및 cuDNN v4 Library for Linux 다운로드
cd /usr/local
sudo tar zxf ~/Downloads/cudnn-7.0-linux-x64-v4.0-prod.tgz
#sudo tar zxf ~/Downloads/cudnn-7.5-linux-x64-v5.1.tgz
cd ~/PKS/deployment/

# Step 4 : Tensorflow
#sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.9.0-cp27-none-linux_x86_64.whl
sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.10.0rc0-cp27-none-linux_x86_64.whl
sudo pip install --upgrade https://ci.tensorflow.org/view/Nightly/job/nightly-matrix-linux-gpu/TF_BUILD_CONTAINER_TYPE=GPU,TF_BUILD_IS_OPT=OPT,TF_BUILD_IS_PIP=PIP,TF_BUILD_PYTHON_VERSION=PYTHON2,label=gpu-linux/lastSuccessfulBuild/artifact/pip_test/whl/tensorflow-0.10.0rc0-cp27-none-linux_x86_64.whl


# Step 5 : Python Library
sudo pip install --upgrade matplotlib
sudo pip install --upgrade pandas
sudo pip install --upgrade seaborn
