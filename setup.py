from setuptools import setup

install_requires = []
dependency_links = []

with open('./requirements.txt') as requirements_txt:
    requirements = requirements_txt.read().strip().splitlines()
    for requirement in requirements:
        if requirement.startswith('#'):
            continue
        elif requirement.startswith('-e '):
            install_requires.append(requirement.split('=')[1])
            dependency_links.append(requirement[3:])
        else:
            install_requires.append(requirement)

print(install_requires)

setup(
    name='cove',
    version='0.0.0',
    author='Open Data Services',
    author_email='code@opendataservices.coop',
    packages=['cove', 'cove.input', 'cove.dataload'],
    scripts=['manage.py'],
    url='https://github.com/OpenDataServices/cove',
    description='',
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    ],
    install_requires=install_requires,
    dependency_links=dependency_links
)
