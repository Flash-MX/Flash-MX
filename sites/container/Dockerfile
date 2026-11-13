# Dockerfile for the Flash-X "container" test site.
#
# Builds an image with AMReX + HYPRE (and HDF5/MPI/Bittree) preinstalled at the
# paths expected by sites/container/Makefile.h, plus the Flash-X-Test framework
# (flashxtest). The GitHub Actions workflows in .github/workflows/container*.yml
# run the suite inside a container built from this image.
#
# This file is for one-time setups that should be cached between commits. Tests
# that exercise Flash-X source diffs run via flashxtest in the workflows, not here.
#
# Library paths MUST match sites/container/Makefile.h:
#   AMREX_PATH = /home/lib/amrex/{1D,2D,3D}
#   HYPRE_PATH = /home/lib/hypre

# Start from ubuntu base image
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

# Upgrade and update distribution
RUN apt-get update && apt-get -y dist-upgrade

# Installation of compilers, tools, and libraries from ubuntu distribution.
# libhdf5-openmpi-dev provides the parallel wrappers h5pfc / h5pcc used by Makefile.h.
RUN apt-get install -y python3 python3-pip gfortran build-essential \
    libhdf5-openmpi-dev openmpi-bin pkg-config libopenmpi-dev \
    libblas-dev liblapack-dev libpnetcdf-dev git python-is-python3 curl tar rsync

# Installation of python packages and the Flash-X-Test framework (flashxtest)
RUN pip3 install numpy matplotlib h5py scipy configparser
RUN pip3 install git+https://github.com/Flash-X/Flash-X-Test.git@020920ca9c59ab7c08089a190b331af98c85090b
RUN chmod 777 /usr/local/lib/python3.10/dist-packages/FlashXTest/backend/FlashTest/ERROR

# Install bittree from source (needed for paramesh-based configs)
RUN git clone https://github.com/Flash-X/Bittree.git --branch v2.0 /Bittree
WORKDIR /Bittree
RUN python3 setup.py library --dim 2 --prefix /Bittree/install/2D
RUN cd build && make && make install && cd ..
RUN python3 setup.py library --dim 3 --prefix /Bittree/install/3D
RUN cd build && make && make install && cd ..

# Installation of AMReX from source into the paths expected by Makefile.h
RUN git clone https://github.com/AMReX-Codes/amrex.git --branch 23.11 /Amrex
WORKDIR /Amrex
RUN ./configure --prefix=/home/lib/amrex/1D --dim=1 && make -j"$(nproc)" && make install
RUN ./configure --prefix=/home/lib/amrex/2D --dim=2 && make -j"$(nproc)" && make install
RUN ./configure --prefix=/home/lib/amrex/3D --dim=3 && make -j"$(nproc)" && make install

# Install hypre from source into the path expected by Makefile.h
RUN git clone https://github.com/hypre-space/hypre.git --branch v2.22.0 /Hypre
WORKDIR /Hypre
RUN cd src && ./configure --enable-shared --enable-fortran --with-MPI --prefix=/home/lib/hypre && make install
ENV LD_LIBRARY_PATH="/home/lib/hypre/lib:${LD_LIBRARY_PATH:-}"
ENV DYLD_LIBRARY_PATH="/home/lib/hypre/lib:${DYLD_LIBRARY_PATH:-}"


# Run container as a non-root user. flashxtest refuses to run as root.
# uid 1001 matches the GitHub Actions runner uid so the mounted workspace
# (owned by the runner) is writable from inside the container.
ENV USER=flashx
ENV LOGNAME=flashx
RUN adduser --uid 1001 --disabled-password --gecos "" $USER
USER $USER
ENV HOME=/home/flashx
# Install Claude Code into the image so the agent does not fetch it at runtime.
RUN curl -fsSL https://claude.ai/install.sh | bash -s -- 2.1.322
ENV PATH="/home/flashx/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
WORKDIR /home/flashx
