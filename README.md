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

目前只支持将数据库安装在d:\mongodb\data\db目录下。NTService依赖于此路径。
		
1.以管理员方式，运行cmd.exe，安装FirstService服务：用于避免系统异常关闭时mongodb2.0的无法自动启动的问题。
		"NTService.exe -i"
2.安装MongoDB服务：
		"D:\mongodb\bin\mongod.exe" --install --dbpath  "d:\MongoDB\data\db"  --logpath  "d:\MongoDB\data\logs\ffs.log"  --directoryperdb 
3.再运行： 
		"sc config MongoDB depend= FirstService"
		"net start MongoDB"
注意“=”和FirstService中间有个空格，否则命令失败。
去掉--logappend。
由于安装服务需要管理员权限，所以请以管理员方式运行控制台cmd.exe程序。
 
4.Babel翻译
4.1设置 Babel
接下来我们要做的是 babel 的配置。在 hello.py 的同级目录创建一个叫 babel.cfg 的文件，内容如下：

    [python: **.py]
    [jinja2: **/templates/**.html]
    extensions=jinja2.ext.autoescape,jinja2.ext.with_

4.2切换到项目的“funfunsay\”目录下（该目录包含translations和templates子目录）。

4.3生成 messages.pot 文件，即生成翻译模板(Win)

    "c:\Python27\Scripts\pybabel.exe extract -F babel.cfg -o messages.pot ."
或(Linux)

    "$ pybabel extract -F babel.cfg -o messages.pot ."
如果使用了lazy_gettext() 函数:

    "$ c:\Python27\Scripts\pybabel.exe extract -F babel.cfg -k lazy_gettext -o messages.pot ."

4.4根据生成的.pot初始化zh_CN的翻译文件

    "c:\Python27\Scripts\pybabel.exe init -i messages.pot -d translations -l zh_CN"
要确保 flask 能找到翻译内容，translations文件夹要和 templates 文件夹在同一个目录中。
然后就可以在.po文件中编辑翻译（不要编辑.pot的文件）翻译结果：

4.5然后编译生成.mo文件

    "c:\Python27\Scripts\pybabel.exe compile -d translations"

如果执行编译命令后出现错误：“UnicodeDecodeError: 'utf8' codec can't decode byte 0xbc in position 8: invalid start byte”，请手动将.po文件另存为utf-8编码后再执行。

4.6如果需要更新翻译，则首先需要用前面4.3的命令重新生成 messages.pot 文件，然后使用下面的命令将更新的内容 merge 到原来的翻译文件（.po）中：

	"c:\Python27\Scripts\pybabel.exe update -i messages.pot -d translations"

当然最后还是要用4.5的命令重新生成.mo文件。
