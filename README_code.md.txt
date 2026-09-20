cd ~
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh


bash Miniforge3-Linux-x86_64.sh

source ~/.bashrc

conda --version

#################################################################################

conda create -n snakemake -c conda-forge -c bioconda snakemake

conda activate snakemake

snakemake --version

#################################################################################################


 فایل دیتابیس از اینجا دانلود کردید

https://data.qiime2.org/classifiers/sklearn-1.4.2/silva/silva-138-99-nb-classifier.qza

بعد در پوشه دیتابیس میزارسد و اسمش رو تغییر میدید به

silva-138-99-classifier.qza


###################################################################################################
اگر Ubuntu/Debian دارید، ابتدا روش بستهٔ رسمی/مناسب سیستم را بررسی کنید. ساده‌ترین روش معمولاً دانلود نسخهٔ باینری از NCBI است:

cd ~/Downloads
wget https://ftp.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-ubuntu64.tar.gz
tar -xzf sratoolkit.current-ubuntu64.tar.gz

سپس وارد پوشه شوید:

cd sratoolkit.*

و مسیر bin را به PATH اضافه کنید:

echo 'export PATH="$PATH:$HOME/Downloads/'"$(basename "$PWD")"'/bin"' >> ~/.bashrc
source ~/.bashrc

برای اطمینان:

fasterq-dump --version

یا:

prefetch --version


##############################################################################



1. نصب pigz
conda install -c conda-forge pigz -y
2. بررسی نصب
pigz --version



##################################
## 2. Install Dependencies

``` bash
sudo apt update
sudo apt install -y wget curl git unzip build-essential python3 python3-pip
```
############################################################################################




## 8. Validate Before Run

``` bash
snakemake --use-conda --conda-frontend mamba --cores 1 -n
```

------------------------------------------------------------------------

## 9. Run Pipeline

Full:

``` bash
snakemake --use-conda --conda-frontend mamba --cores all
```

Resume:

``` bash
snakemake --use-conda --conda-frontend mamba --cores all --rerun-incomplete
```

#################################################################################################





########################
pip install snakefmt
snakefmt rules/
#####################





