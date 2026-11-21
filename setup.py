"""eazy_data_viz 打包配置（pip install . / pip install -e .）。"""
import io
import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with io.open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


setup(
    name="eazy_data_viz",
    version="1.5.0",
    description="给 pandas 用的经营驾驶舱图表库（HTML / Streamlit）：49 种图表、Material Design 3、客户端下钻/联动",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    license="MIT",
    author="eazy_data_viz",
    author_email="jupeter0v0@users.noreply.github.com",
    url="https://github.com/jupeter0v0/eazy_data_viz",
    project_urls={
        "主页 / 示例": "https://github.com/jupeter0v0/eazy_data_viz",
        "问题反馈": "https://github.com/jupeter0v0/eazy_data_viz/issues",
    },
    python_requires=">=3.8",
    packages=find_packages(include=["eazy_data_viz", "eazy_data_viz.*"]),
    package_data={
        "eazy_data_viz": ["assets/*.js", "assets/*.json", "assets/maps/*.json",
                          "gallery/*.html", "gallery/*.py", "fonts/*"],
    },
    include_package_data=True,
    install_requires=["pandas>=1.3"],
    extras_require={
        "streamlit": ["streamlit>=1.10"],
        "notebook": ["ipython>=7"],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    keywords=["pandas", "chart", "visualization", "echarts", "streamlit", "html"],
)
