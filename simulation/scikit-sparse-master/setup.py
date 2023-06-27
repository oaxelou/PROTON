# Copyright (C) 2008-2017 The scikit-sparse developers:
#
# 2008        David Cournapeau        <cournape@gmail.com>
# 2009-2015   Nathaniel Smith         <njs@pobox.com>
# 2010        Dag Sverre Seljebotn    <dagss@student.matnat.uio.no>
# 2014        Leon Barrett            <lbarrett@climate.com>
# 2015        Yuri                    <yuri@tsoft.com>
# 2016-2017   Antony Lee              <anntzer.lee@gmail.com>
# 2016        Alex Grigorievskiy      <alex.grigorievskiy@gmail.com>
# 2016-2017   Joscha Reimer           <jor@informatik.uni-kiel.de>
# 2021-       Justin Ellis            <justin.ellis18@gmail.com>

"""Sparse matrix tools. 

This is a home for sparse matrix code in Python that plays well with
scipy.sparse, but that is somehow unsuitable for inclusion in scipy
proper. Usually this will be because it is released under the GPL.

So far we have a wrapper for the CHOLMOD library for sparse Cholesky
decomposition. Further contributions are welcome!
"""

DISTNAME = "scikit-sparse"
DESCRIPTION = "Scikit sparse matrix package"
LONG_DESCRIPTION = __doc__
MAINTAINER = "Justin Ellis"
MAINTAINER_EMAIL = "justin.ellis18@gmail.com"
URL = "https://github.com/scikit-sparse/scikit-sparse"
LICENSE = "BSD"

import sys

import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

setup(
    install_requires=["numpy>=1.13.3", "scipy>=0.19"],
    python_requires=">=3.6, <3.10",
    packages=find_packages(),
    package_data={
        "": ["test_data/*.mtx.gz"],
    },
    data_files = [
        ('sksparse', [
              ('../../thirdparty/Intel/mkl/2021.2.0/redist/intel64/mkl_avx2.1.dll'),
              ('../../thirdparty/Intel/mkl/2021.2.0/redist/intel64/mkl_core.1.dll'),
              ('../../thirdparty/Intel/mkl/2021.2.0/redist/intel64/mkl_def.1.dll'),
              ('../../thirdparty/Intel/mkl/2021.2.0/redist/intel64/mkl_intel_thread.1.dll'),
              ('../../thirdparty/Intel/compiler/2021.2.0/windows/redist/intel64_win/compiler/libiomp5md.dll'),
        ] ),
      ],
    name=DISTNAME,
    version="0.4.5",  # remember to update __init__.py
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    url=URL,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Cython",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    # You may specify the directory where CHOLMOD is installed using the
    # library_dirs and include_dirs keywords in the lines below.
    ext_modules=cythonize(
        Extension(
            "sksparse.cholmod",
            ["sksparse/cholmod.pyx"],
            include_dirs=[
                np.get_include(),
                sys.prefix + "/include",
                "../../thirdparty/SuiteSparse/SuiteSparse/AMD/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/CAMD/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/CCOLAMD/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/COLAMD/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/CHOLMOD/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/metis-5.1.0/Include",
				"../../thirdparty/SuiteSparse/SuiteSparse/SuiteSparse_config",
                "../../thirdparty/Intel/mkl/2021.2.0/include"
            ],
            library_dirs=["../../thirdparty/Intel/mkl/2021.2.0/lib/intel64",
                          "../../thirdparty/Intel/compiler/2021.2.0/windows/compiler/lib/intel64_win",
                          "../../thirdparty/SuiteSparse/lib/Release"
                          ],
            libraries=[ 'mkl_intel_lp64_dll','mkl_intel_thread_dll', 'mkl_core_dll','libiomp5md','libcholmod', 'libamd', 'libcamd', 'libccolamd', 'libcolamd', 
                         'suitesparseconfig','metis']
        )
    ),
)
