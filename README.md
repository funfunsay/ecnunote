#ecnunote

ecnu note application with an android client.

##~ How do I use it?

Go to source code root directory, and 
Run local server: ::

    $ python shell.py runserver

or

    $ python shell.py run

the application will greet you on http://localhost:5000/ .
	
##~ Is it tested?

You betcha.  Run the `funfunsay_tests.py` file to see the tests pass.

##~ Setup 

Install packages: ::

    $ python setup.py install	

Compile with babel: ::
    
    $ python setup.py compile_catalog --directory fbone/translations --locale zh -f

Ŀǰֻ֧�ֽ����ݿⰲװ��d:\mongodb\data\dbĿ¼�¡�NTService�����ڴ�·����
		
1.�Թ���Ա��ʽ������cmd.exe����װFirstService�������ڱ���ϵͳ�쳣�ر�ʱmongodb2.0���޷��Զ����������⡣
		"NTService.exe -i"
2.��װMongoDB����
		"D:\mongodb\bin\mongod.exe" --install --dbpath  "d:\MongoDB\data\db"  --logpath  "d:\MongoDB\data\logs\ffs.log"  --directoryperdb 
3.�����У� 
		"sc config MongoDB depend= FirstService"
		"net start MongoDB"
ע�⡰=����FirstService�м��и��ո񣬷�������ʧ�ܡ�
ȥ��--logappend��
���ڰ�װ������Ҫ����ԱȨ�ޣ��������Թ���Ա��ʽ���п���̨cmd.exe����
 
4.Babel����
4.1���� Babel
����������Ҫ������ babel �����á��� hello.py ��ͬ��Ŀ¼����һ���� babel.cfg ���ļ����������£�

    [python: **.py]
    [jinja2: **/templates/**.html]
    extensions=jinja2.ext.autoescape,jinja2.ext.with_

4.2�л�����Ŀ�ġ�funfunsay\��Ŀ¼�£���Ŀ¼����translations��templates��Ŀ¼����

4.3���� messages.pot �ļ��������ɷ���ģ��(Win)

    "c:\Python27\Scripts\pybabel.exe extract -F babel.cfg -o messages.pot ."
��(Linux)

    "$ pybabel extract -F babel.cfg -o messages.pot ."
���ʹ����lazy_gettext() ����:

    "$ c:\Python27\Scripts\pybabel.exe extract -F babel.cfg -k lazy_gettext -o messages.pot ."

4.4�������ɵ�.pot��ʼ��zh_CN�ķ����ļ�

    "c:\Python27\Scripts\pybabel.exe init -i messages.pot -d translations -l zh_CN"
Ҫȷ�� flask ���ҵ��������ݣ�translations�ļ���Ҫ�� templates �ļ�����ͬһ��Ŀ¼�С�
Ȼ��Ϳ�����.po�ļ��б༭���루��Ҫ�༭.pot���ļ�����������

4.5Ȼ���������.mo�ļ�

    "c:\Python27\Scripts\pybabel.exe compile -d translations"

���ִ�б����������ִ��󣺡�UnicodeDecodeError: 'utf8' codec can't decode byte 0xbc in position 8: invalid start byte�������ֶ���.po�ļ����Ϊutf-8�������ִ�С�

4.6�����Ҫ���·��룬��������Ҫ��ǰ��4.3�������������� messages.pot �ļ���Ȼ��ʹ�������������µ����� merge ��ԭ���ķ����ļ���.po���У�

	"c:\Python27\Scripts\pybabel.exe update -i messages.pot -d translations"

��Ȼ�����Ҫ��4.5��������������.mo�ļ���
