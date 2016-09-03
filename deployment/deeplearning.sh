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

# Step 3 : CUDNN
# https://developer.nvidia.com/rdp/cudnn-download 에 접속
# 로그인 및 cuDNN v4 Library for Linux 다운로드
cd /usr/local
sudo tar zxf ~/Downloads/cudnn-7.0-linux-x64-v4.0-prod.tgz
cd ~/PKS/deployment/

# Step 4 : Tensorflow (0.9. 0.10 은 아직 rc 단계)
sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.9.0-cp27-none-linux_x86_64.whl

# Step 5 : Theano
sudo pip install nose
sudo pip install Theano
cp .theanorc ~

# Step 6 : Downgrade g++
# CUDA 7.5 는 아직 최신 버전 g++ 과는 호환이 안됨
sudo apt install g++-4.9
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.9 20
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-5 10
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.9 20
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-5 10
sudo update-alternatives --install /usr/bin/cc cc /usr/bin/gcc 30
sudo update-alternatives --set cc /usr/bin/gcc
sudo update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++ 30
sudo update-alternatives --set c++ /usr/bin/g++

# Step 7 : Keras
sudo pip install keras
sudo apt install libopencv-dev python-opencv
sudo pip install h5py

# Step 8 : Caffe
sudo apt install libprotobuf-dev libleveldb-dev libsnappy-dev libhdf5-serial-dev protobuf-compiler
sudo apt install --no-install-recommends libboost-all-dev
sudo apt install libgflags-dev libgoogle-glog-dev liblmdb-dev
# https://developer.nvidia.com/rdp/cudnn-download 에 접속
# 로그인 및 cuDNN v5 Library for Linux 다운로드
cd /usr/local
sudo tar zxf ~/Downloads/cudnn-7.5-linux-x64-v5.0-ga.tgz
cd ~/git/
git clone https://github.com/BVLC/caffe
cd caffe/
sudo -H pip install -r python/requirements.txt --upgrade
cp Makefile.config.example Makefile.config
sudo apt install cmake
vi Makefile.config
