# 
FROM python:3.10

# 
WORKDIR /code

# 把当前文件夹的所有文件复制到工作文件夹
COPY . /code/

# 
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip config set global.extra-index-url "http://mirrors.aliyun.com/pypi/simple/ https://pypi.mirrors.ustc.edu.cn/simple/ http://pypi.hustunique.com/ http://pypi.douban.com/simple/ http://pypi.sdutlinux.org/"
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN apt-get update && apt-get install -y nano

# 复制字体文件到容器中
COPY static/resources/fonts/STSONG.TTF /usr/local/lib/python3.10/site-packages/matplotlib/mpl-data/fonts/ttf/

# 运行命令
RUN cd ~/.cache/matplotlib && rm * -r

# 
CMD ["python","main.py"]