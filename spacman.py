#!/usr/bin/env python
#-*- encoding:utf-8 -*-

import os
import sys
import ctypes
import argparse
import copy


default_conf_file = os.path.expanduser('~') + '/.config/spacman/default.conf'
# default_conf_file = '/etc/spacman/default.conf'


class packageManager:
    def get_default_pkg_manager(self):
        # 默认包管理器
        assert 0

    def install(self, pkg_manager, pkg_list):
        # 调用包管理器安装软件
        # pkg_manager 是传递进来的默认 -p 参数
        # pkg_list 是软件列表
        assert 0

    def uninstall(self, pkg_manager, pkg_list):
        # 调用包管理器卸载软件
        # pkg_manager 是传递进来的默认 -p 参数
        # pkg_list 是软件列表
        assert 0

    def readAllPkgInfo(self):
        # 获取系统中所有的包信息
        # 返回的结果形如
        #   {"包名":信息,"包名":信息,...}
        assert 0

    def toDepenndsListDict(self, infoDict):
        # 将上述 readAllPkgInfo 返回的格式翻译成包依赖列表
        # 返回的结果形如
        #   {
        #    "包名":[{"包1","包2",...},{"包1","包2",...},...],
        #    "包名":[{"包1","包2",...},{"包1","包2",...},...],
        #    ...
        #   }
        # 其中，集合内是或的关系，列表中的与的关系
        assert 0


class pmDEB(packageManager):
    def get_default_pkg_manager(self):
        assert 0

    def install(self, pkg_manager, pkg_list):
        assert 0

    def uninstall(self, pkg_manager, pkg_list):
        assert 0

    def readAllPkgInfo(self):
        assert 0
        
    def toDepenndsListDict(self, infoDict):
        assert 0


class pmRPM(packageManager):
    def get_default_pkg_manager(self):
        assert 0

    def install(self, pkg_manager, pkg_list):
        assert 0

    def uninstall(self, pkg_list):
        assert 0

    def readAllPkgInfo(self):
        assert 0
        
    def toDepenndsListDict(self, infoDict):
        assert 0


class pmPACMAN(packageManager):
    def get_default_pkg_manager(self):
        return 'sudo pacman'

    def install(self, pkg_manager, pkg_list):
        os.system(pkg_manager + ' -S ' + ' '.join(pkg_list))

    def uninstall(self, pkg_manager, pkg_list):
        os.system(pkg_manager + ' -R ' + ' '.join(pkg_list))

    def readAllPkgInfo(self):
        def conv_pkg_info(pkg_info_str):
            return [pkg_info_str[0][1], [pkg_info_str[1][1], pkg_info_str[7][1].split(), pkg_info_str[8][1].split()]]
        
        pkg_info_list = os.popen('LANG=C pacman -Qi').read().strip().replace(' None', '').split('\n\n')
        result = dict(map(
            lambda i:conv_pkg_info(list(map(
                lambda l:list(map(
                    lambda ll:ll.strip(),
                    l.split(' :'))),
                i.split('\n')))),
            pkg_info_list))
        return result
        
    def toDepenndsListDict(self, infoDict):
        
        # 计算出以“提供”为键的字典
        # 格式为
        #     {"提供名": {"哪个包提供": "提供的版本号",...},...}
        pkg_provider_dict = dict()
        for pkg in infoDict:
            provider_list = list(map(lambda x:x.split('='), infoDict[pkg][1]))
            for provider in provider_list:
                if provider[0] not in pkg_provider_dict:
                    pkg_provider_dict[provider[0]] = dict()
                
                if len(provider) == 1:
                    pkg_provider_dict[provider[0]][pkg] = None
                else:
                    pkg_provider_dict[provider[0]][pkg] = provider[1]
        
        # 定义版本比较函数
        libalpm = ctypes.CDLL('libalpm.so')
        alpm_pkg_vercmp = libalpm.alpm_pkg_vercmp
        def vercmp(v1, v2):
            return alpm_pkg_vercmp(ctypes.c_char_p(v1.encode()),ctypes.c_char_p(v2.encode()))
        
        # 开始解析依赖
        result = dict()
        for pkg in infoDict:
            result[pkg] = []
            for needstr in infoDict[pkg][2]:
                need_set = set()
                
                # 以符号为分隔符，分离出需要和版本号
                for op in ['<=', '>=', '<', '>', '=']:
                    need = needstr.split(op)
                    if len(need) != 1:
                        if op == '=':
                            op = '=='
                        break;
                
                if len(need) > 2:
                    sys.stderr.write('Error: The dependency of ' + pkg + ' "' + \
                        needstr + '" can\'t be parsed. Please report this BUG."\n')
                    continue
                
                # 所需的包在真实的包名里找到
                if need[0] in infoDict:
                    if len(need) == 1:
                        need_set.add(need[0])
                    else:
                        cmpr = vercmp(infoDict[need[0]][0], need[1])
                        if eval('cmpr ' + op + ' 0'):
                            need_set.add(need[0])
                
                # 所需的包在提供字典里找到
                if need[0] in pkg_provider_dict:
                    
                    if len(need) == 1:
                        # 如果无版本要求，则所有提供这个的包都列入可选包
                        need_set |= set(pkg_provider_dict[need[0]])
                    else:
                        # 如果有版本要求，则将所有提供这个的包进行版本对比
                        for p_pkg in pkg_provider_dict[need[0]]:
                            p_pkg_ver = pkg_provider_dict[need[0]][p_pkg]
                            if p_pkg_ver is None:
                                # 如果软件包没指明提供的版本，则直接加入
                                need_set.add(p_pkg)
                            else:
                                cmpr = vercmp(p_pkg_ver, need[1])
                                if eval('cmpr ' + op + ' 0'):
                                    need_set.add(p_pkg)
                
                if len(need_set) == 0:
                    sys.stderr.write('Error: The dependency of ' + pkg + ' "' + \
                        needstr + '" can\'t be satisfied. Please check."\n')
                else:
                    result[pkg].append(need_set)
        
        return result

class packageManagerFactory:
    def get(self):
        # 返回包管理器类对象
        
        def has(command):
            # 判断系统中是否有这条命令
            return os.system('sh -c "type -p ' + command + '" >/dev/null') == 0
        
        def tot(command):
            # 统计一条命令输出结果的行数
            return int(os.popen(
                r'sh -c "read -d \"\" -ra pkgs <<< \"\$(' + command + r')\";printf \${#pkgs[@]}"'
                ).read())
        
        max_tot = 0
        result = None
        
        # 检查 pacman 包管理器
        if has('pacman-key'):
            now_tot = tot('pacman -Qq --color never')
            if now_tot > max_tot:
                max_tot = now_tot
                result = pmPACMAN
        
        # 检查 deb 包管理器
        if has('dpkg'):
            now_tot = tot(r"dpkg-query -f '.\n' -W")
            if now_tot > max_tot:
                max_tot = now_tot
                result = pmDEB
        
        # 检查 rpm 包管理器
        if has('rpm'):
            now_tot = tot("rpm -qa")
            if now_tot > max_tot:
                max_tot = now_tot
                result = pmRPM
        
        return result()


class coreCalc:
    def solveMin(self, pkgs_depends_dict, pkg_in_config):
        # 核心算法，输入依赖结构和需求列表集合，输出最小需求包集合

        """
            从顶层开始一层一层的向下迭代，逐渐将确定的依赖，加入结果中
            top_c_pkg   表示待计算的需求集合，需要将他们的依赖加入列表
            result      表示已经处理过的包集合。
            new_c_pkg   表示下一轮循环需要加入 top_c_pkg 的包
            finished_c_pkg 表示这一轮结束之后需要移入 result 的包
        """
        result = set()
        top_c_pkg = pkg_in_config.copy()
        while len(top_c_pkg) > 0: # 每循环一轮，处理了一次 top_c_pkg ，直到 top_c_pkg 为空，或者存在多个解导致无法处理下去
            new_c_pkg = set()
            finished_c_pkg = set()
            for top_pkg in top_c_pkg: # 遍历里面所有的包
                pkg_req_c_finished = True  # 表示此包是否被处理完，当后续还存在多个“或”关系的多个解时，会将此开关设为 False
                for deps in pkgs_depends_dict[top_pkg]:  # 遍历所有“与”关系的依赖
                    pkg_and_c_pass = False  # 表示此依赖是否已经确定，当后续确定时，会将此开关设为 True
                    if len(deps) == 1:  # 将只有一个“或”关系的依赖定义为必要的包
                        pkg = tuple(deps)[0]
                        pkg_and_c_pass = True  # 如果必要的包不在待计算的里面，则直接确定 pkg_and_c_pass
                        if not (pkg in result or pkg in top_c_pkg or pkg in new_c_pkg):
                            new_c_pkg.add(pkg)
                    else:
                        for or_deps in deps:  # 存在多个包“或”关系的包时，看是否能确定 pkg_and_c_pass
                            if or_deps in result or or_deps in top_c_pkg or or_deps in new_c_pkg:
                                pkg_and_c_pass = True
                                break
                    
                    if not pkg_and_c_pass:
                        pkg_req_c_finished = False
                
                if pkg_req_c_finished: # 将处理完的顶层包准备加入 result
                    finished_c_pkg.add(top_pkg)
            
            # 本轮结束，后续处理
            result |= finished_c_pkg
            top_c_pkg = (top_c_pkg | new_c_pkg) - finished_c_pkg

            # 如果无法进行下去
            if len(finished_c_pkg) == 0 and len(new_c_pkg) == 0:
                break

        if len(top_c_pkg) != 0:
            or_result = []
            for top_pkg in top_c_pkg:
                for deps in pkgs_depends_dict[top_pkg]:
                    if len(deps) > 1:
                        for or_deps in deps:
                            if or_deps in result or or_deps in top_c_pkg:
                                break
                        else:
                            or_result.append(deps)
            return result, top_c_pkg

        return result

class spacmanController:
    def get_conf_set(self, config):
        # 从配置文件中读取包名，返回包名集合
    
        lines = open(config).readlines()
        s_set = set()
        for line in lines:
            elem = line.split('#', 1)[0].strip()
            if len(elem) != 0:
                s_set.add(elem)
        return s_set

    def main(self, args):
        # 主控制逻辑函数

        # 输出函数
        def output(info_str, color_str, pkg_set):
            print(info_str % len(pkg_set))
            pkg_list = list(pkg_set)
            pkg_list.sort()
            print('\033[' + color_str + 'm' + ' '.join(pkg_list) + '\033[0m')

        # 检查配置文件
        if not os.path.exists(args.config):
            sys.stderr.write('No such file: ' + args.config + '\n')
            return 1

        # 读取配置文件
        pkg_in_config = spacmanController().get_conf_set(args.config)
        if args.query:
            print('\n'.join(pkg_in_config))
            return 0

        # 判断系统的包管理器类型
        PM = packageManagerFactory().get()
        if PM is None:
            sys.stderr.write('Cannot get the type of the package manager.\n')
            return 1

        # 设置包管理器参数
        if args.pacman is None:
            args.pacman = PM.get_default_pkg_manager()

        # 读取系统里所有的包名及其信息
        system_pkg_info = PM.readAllPkgInfo()
        pkg_in_system = set(system_pkg_info)

        # 判断设置文件中是否有某个包未装
        pkg_need_install = pkg_in_config - pkg_in_system
        if pkg_need_install != set():
            if args.ignore:
                pkg_in_config -= pkg_need_install
            else:
                if args.apply:
                    PM.install(args.pacman, pkg_need_install)
                else:
                    output('Following %d packages need to be installed:', '1;32', pkg_need_install)
                    return 0

        # 解析依赖，翻译成统一的“与”“或”依赖格式
        pkgs_depends_dict = PM.toDepenndsListDict(system_pkg_info)

        # 接下来开始进行核心计算
        pkg_min_set = coreCalc().solveMin(pkgs_depends_dict, pkg_in_config)

        # 如果核心运算存在多个解
        if type(pkg_min_set) == list:
            for pkgs in pkg_min_set:
                output("There are %d choices, please choose one.", '1;45', pkgs)
            return 0

        # 求出多余的包
        pkg_noneeds_set = pkg_in_system - pkg_min_set

        if args.apply:
            # 直接卸载的这些包
            PM.uninstall(args.pacman, pkg_noneeds_set)
        else:
            # 直接打印需要卸载的包
            output('Following %d packages need to be uninstalled:', '1;33', pkg_noneeds_set)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Super package manager for archlinux.")
    parser.add_argument('--config', '-c', help='Specify the package list file. The default is ' + default_conf_file, default=default_conf_file)
    parser.add_argument('--pacman', '-p', help='Specify the package management.', default=None)
    parser.add_argument('--ignore', '-i', help='Ignored packages in configure file that were not installed.', action='store_const', const=True, default=False)
    parser.add_argument('--apply', '-a', help='Call package manager to apply to system.', action='store_const', const=True, default=False)
    parser.add_argument('--query', '-q', help='Query packages from the configure file.', action='store_const', const=True, default=False)
    args = parser.parse_args()
    
    exit(spacmanController().main(args))




