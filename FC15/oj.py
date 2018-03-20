#coding=utf-8
import os, time, random
import threading
from FC15.models import FileInfo, AIInfo, GameRecord
from queue import Queue # Python3
#from Queue import Queue # Python2


#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


IS_RUNNING = 0
GAME_RUNNING = 0
#COMPILE_MODE = 'VS'
COMPILE_MODE = 'G++'
FILE_SUFFIX = 'so'
RECORD_SUFFIX = 'json' # maybe should be changed to 'json'
DEFAULT_RECORD_FILENAME = 'log.json'
# FILE_SUFFIX = 'exe'
GAME_QUEUE = Queue()


class SingleGameInfo(object):
    username = ''
    ai_list = []


# Start running
def run():
    global IS_RUNNING
    if IS_RUNNING == 0:
        IS_RUNNING = 1
        t = threading.Thread(target = compile_all)
        t.start()


def run_game_queue():
    global GAME_RUNNING
    if GAME_RUNNING == 0:
        GAME_RUNNING = 1
        t = threading.Thread(target = run_allgame)
        t.start()


# Run all games in the queue, should be put into a new thread
def run_game():
    global GAME_RUNNING
    global GAME_QUEUE
    if GAME_RUNNING == 0:
        return
    while GAME_QUEUE.empty() == False:
        gameinfo = GAME_QUEUE.get()
        # Launch game
        result = launch_game(gameinfo.ai_list, gameinfo.username)
        # Generate game record
        record = GameRecord()
        record.username = gameinfo.username
        record.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if result == 0:
            record.state = 'Success'
        elif result == -1:
            record.state = 'Failed to Launch game'
        elif result == 1:
            record.state = 'Runtime Error'
        else:
            record.state = 'Unknown state'
        now = time.strftime('%Y%m%d%H%M%S')
        file_name = 'record{0}_{1}.{2}'.format(now, random.randint(0, 1000), RECORD_SUFFIX)
        while os.path.exists('gamerecord/{0}'.format(file_name)):
            file_name = 'record{0}_{1}.{2}'.format(now, random.randint(0, 1000), RECORD_SUFFIX)
        destin_dir = 'gamerecord/' + file_name
        source_dir = 'playgame/log_json/' + DEFAULT_RECORD_FILENAME
        # Copy record file
        if os.path.exists(source_dir):
            open(destin_dir, 'wb').write(open(source_dir, 'rb').read())
            open('static/' + destin_dir, 'wb').write(open(source_dir, 'rb').read())
            try:
                os.remove(source_dir) # delete source file, avoid problems when playing game next time (sometimes the sample 'logic' fails to create record file)
            except:
                pass
        else:
            record.state = 'Failed to Launch game'
        record.filename = file_name
        record.save()
    GAME_RUNNING = 0


# Copy file
def copy_file(username, file_name):
    global COMPILE_MODE
    source_dir = 'fileupload/{0}/{1}'.format(username, file_name)
    if COMPILE_MODE == 'VS':
        destin_dir = 'cpp_proj/ai/ai.cpp'
    if COMPILE_MODE == 'G++':
        destin_dir = 'AI_SDK/ai.cpp'
    if os.path.isfile(source_dir):
        open(destin_dir, 'wb').write(open(source_dir, 'rb').read())
        return True
    else:
        return False


# Copy executable file
def copy_exe(username, file_name):
    global FILE_SUFFIX
    global COMPILE_MODE
    if COMPILE_MODE == 'VS':
        source_dir = 'cpp_proj/Release/ai.' + FILE_SUFFIX
    if COMPILE_MODE == 'G++':
        source_dir = 'AI_SDK/ai.' + FILE_SUFFIX
    destin_dir = 'fileupload/{0}/{1}.{2}'.format(username, file_name[:-3], FILE_SUFFIX)
    if os.path.isfile(source_dir):
        open(destin_dir, 'wb').write(open(source_dir, 'rb').read())
        return True
    else:
        return False


# Copy executable file to /playgame directory
def store_exe(username, file_name, pk):
    global FILE_SUFFIX
    global COMPILE_MODE
    source_dir = 'fileupload/{0}/{1}.{2}'.format(username, file_name[:-3], FILE_SUFFIX)
    destin_dir = 'playgame/lib_ai/{0}.{1}'.format(pk, FILE_SUFFIX)
    if os.path.isfile(source_dir):
        if os.path.exists(destin_dir):
            os.remove(destin_dir)
        open(destin_dir, 'wb').write(open(source_dir, 'rb').read())
        return True
    else:
        return False


# Delete copied executable file in /playgame directory
def delete_exe(file_object):
    global FILE_SUFFIX
    if file_object.is_compile_success == 'Successfully compiled':
        if os.path.exists('/playgame/lib_ai/{0}.{1}'.format(file_object.pk, FILE_SUFFIX)):
            os.remove('/playgame/lib_ai/{0}.{1}'.format(file_object.pk, FILE_SUFFIX))


# Compile all the file
def compile_all():
    global IS_RUNNING
    if IS_RUNNING == 0:
        return
    is_done = True
    while is_done:
        is_done = False
        all_file = FileInfo.objects.all()
        for file in all_file:
            if file.is_compiled == 'Not compiled':
                is_done = True
                copy_result = copy_file(file.username, file.exact_name)
                if copy_result:
                    # use visual studio to compile the project
                    global COMPILE_MODE
                    if COMPILE_MODE == 'VS':
                        compile_result = os.system('devenv cpp_proj/ai.sln /rebuild > result.txt')
                    if COMPILE_MODE == 'G++':
                        #compile_result = os.system('g++ AI_SDK/definition.cpp AI_SDK/ai.cpp -o AI_SDK/ai.' + FILE_SUFFIX)
                        #compile_result = os.system('g++ -std=c++11 AI_SDK/definition.cpp AI_SDK/ai.cpp -fPIC -shared -o ai.so')
                        compile_result = os.system('./compile_ai') # use shell 
                    file.is_compiled = 'Compiled'
                #if compile_result == 0:
                if os.path.exists('AI_SDK/ai.so'):
                    file.is_compile_success = 'Successfully compiled'
                    copy_exe(file.username, file.exact_name)
                    store_exe(file.username, file.exact_name, file.pk)
                    os.remove('AI_SDK/ai.so')
                else:
                    file.is_compile_success = 'Compile Error'
                file.save()
    IS_RUNNING = 0


def run_allgame():
    global GAME_RUNNING
    if GAME_RUNNING == 0:
        return
    is_done = True
    while is_done:
        is_done = False
        all_record = GameRecord.objects.all()
        for record in all_record:
            # ==========================================
            print('Currently running: username={0}, timestamp={1}'.format(record.username, record.timestamp))

            if record.state == 'Unstarted':
                is_done = True
                ai1 = record.AI1
                ai2 = record.AI2
                ai3 = record.AI3
                ai4 = record.AI4
                # Edit config file
                file = '/home/songjh/playgame/config_gnu.ini'

                print('Running game, with ai_list = [{0}, {1}, {2}, {3}], username = {4}'.format(ai1, ai2, ai3, ai4, record.username))

                with open(file, 'w') as f:
                    f.write('../map/map_2.txt\n')
                    f.write('4\n')
                    f.write('../lib_ai/{0}.so\n'.format(ai1.strip()))
                    f.write('../lib_ai/{0}.so\n'.format(ai2.strip()))
                    f.write('../lib_ai/{0}.so\n'.format(ai3.strip()))
                    f.write('../lib_ai/{0}.so\n'.format(ai4.strip()))
                    f.write(record.AI1_name.strip() + '\n')
                    f.write(record.AI1_name.strip() + '\n')
                    f.write(record.AI1_name.strip() + '\n')
                    f.write(record.AI1_name.strip() + '\n')

                # Launch main logic, using shell
                os.system('./run_logic')
                # Copy record file is possible
                source_dir = '/home/songjh/playgame/log_json/log.json'
                destin_dir = '/home/songjh/gamerecord/{0}'.format(record.filename)
                destin_dir2 = '/home/songjh/static/gamerecord/{0}'.format(record.filename)
                if os.path.exists(source_dir):
                    record.state = 'Success'
                    open(destin_dir, 'wb').write(open(source_dir, 'rb').read())
                    open(destin_dir2, 'wb').write(open(source_dir, 'rb').read())
                    os.remove(source_dir)
                else:
                    record.state = 'Failure'
                record.save()
    GAME_RUNNING = 0


# Copy all available executable file
def copy_all_exe():
    file_available = FileInfo.objects.filter(is_compile_success__exact = 'Successfully compiled')
    for file in file_available:
        store_exe(file.username, file.exact_name, file.pk)


# Add game infomation into waiting queue
def play_game(ai_list, username):
    global GAME_RUNNING
    queue_item = SingleGameInfo()
    queue_item.ai_list = ai_list
    queue_item.username = username
    print('Queue add: username={0}, ai_list='.format(username)) #+=======================
    print(ai_list)
    GAME_QUEUE.put(queue_item)
    if GAME_RUNNING == 0:
        GAME_RUNNING = 1
        t = threading.Thread(target = run_game)
        t.start()


# Launch logic once
def launch_game(ai_list, username):
    #exe_path = 'playgame/bin/main_logic' # should be 'playgame/logic.exe' on Ubuntu

    # parameters and there should be more
    startgame_failure = -1
    result_success = 0
    result_runtimeerror = 1

    os.system('./run_logic') #=======================================
    print('current_run: ai_list=')
    print(ai_list)
    print('username={0}'.format(username))
    #cmd = exe_path
#    if ai_list:
#        # genereate command to launch logic
#        #for item in ai_list:
#        #    cmd = cmd + '{0} '.format(item)
#        # launch logic
#
#        CREATE_INI_FILE = True
#        # Output AI_list to config file
#        if CREATE_INI_FILE:
#            f = open('/home/songjh/playgame/config_gnu.ini', 'w')
#            f.write('../map/map_2.txt\n') # If the map is to change, this line should be changed
#            f.write('4\n')
#            for item in ai_list:
#                f.write('../lib_ai/{0}.so\n'.format(item.strip()))
#
#        # Use shell to start main logic or it may fail to read .ini file
#        result = os.system('./run_logic')
#        print('Launch: result = {0}'.format(result))
#        return result
#    else:
#        return startgame_failure


def write_log(log_str):
    file = 'server.log'
    with open(file, 'w+') as f:
        f.write(log_str)
