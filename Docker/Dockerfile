FROM tensorflow/tensorflow:2.4.1-gpu

RUN apt-get update && apt-get install -y \
	git \
	libx11-6 \
	libgl1 \
	libopengl0 \
	libegl1 \
	wget

WORKDIR /usr/local/lib/python3.6/dist-packages/

RUN wget https://github.com/DCBIA-OrthoLab/fly-by-cnn/releases/download/2.0/vtk8.2.0.zip
RUN	unzip vtk8.2.0.zip

RUN pip install itk sklearn pandas matplotlib

WORKDIR /app

RUN git clone https://github.com/DCBIA-OrthoLab/fly-by-cnn.git

#RUN wget https://github.com/DCBIA-OrthoLab/fly-by-cnn/releases/download/2.1/u_seg_nn_v3.0.zip
#RUN unzip u_seg_nn_v3.0.zip
RUN wget https://github.com/DCBIA-OrthoLab/fly-by-cnn/releases/download/2.2/u_seg_nn_v3.1.zip
RUN unzip u_seg_nn_v3.1.zip


ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.6/dist-packages/vtkmodules/
ENV MESA_GL_VERSION_OVERRIDE=3.2
