from setuptools import setup, find_packages

setup(
    name='crypto_market_bot',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot[job-queue]==20.7',
        'requests==2.31.0',
        'beautifulsoup4==4.12.2',
        'matplotlib==3.8.2',
        'python-dotenv==1.0.0',
        'aiohttp==3.9.1',
        'SQLAlchemy==2.0.23',
    ],
    python_requires='>=3.8',
)
