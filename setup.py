import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='django-ipfields',
    version='0.0.1',
    author='Francisco Altoe',
    author_email='franciscoda@outlook.com',
    description='IP address and network fields for django',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/FranciscoDA/django-ipfields',
    packages=setuptools.find_packages(),
    classifiers=[],
    install_requires=['django'],
    python_requires='>=3.6',
)