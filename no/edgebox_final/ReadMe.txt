1205版本
1. 安裝項目環境 
   1.1 安裝python3.5+版本解釋器 
   1.2 安裝Virtualenv（用於創建虛擬環境的包）
   1.3 為項目安裝後台環境 python35 -m Virtualenv edgebox_final(環境名)
   1.4 激活項目環境 cd edgebox_final/Scripts   .activate
   1.5 離線安裝依賴包 python -m pip install --no-index -f ./whls(離線包位置) -r pkg.txt(包名) 
2. 啟動環境
   2.1 激活項目環境 cd edgebox_final/Scripts   .activate
   2.2 啟動Django python manage.py runserver 0.0.0.0:8002(端口目前與Vue一致8002)
   2.3 啟動celery任務 python manage.py celeryd -l info 
   2.4 啟動celery定時任務 python manage.py celerybeat -l info （不啟動它，也可以work ,用於M5模塊）
3. 導出項目環境 (未必要)
   3.1 激活項目環境 cd edgebox_final/Scripts   .activate
   3.2 使用pip管理器導出項目依賴包 pip freeze ->pkg.txt
   3.3 使用pip管理器在線下載項目依賴包 pip download -r pkg.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
