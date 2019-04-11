#!/usr/bin/python3

import os

conf_file = os.path.expanduser('~') + '/.config/spacman.conf'

def conv_pkg_info(pkg_info_str):
    return [pkg_info_str[0][1], [pkg_info_str[1][1], pkg_info_str[7][1].split(), pkg_info_str[8][1].split()]]

def get_system_pkgs():
    
    # 
    pkg_info_list = os.popen('LANG=C pacman -Qi').read().strip().replace(' None', '').split('\n\n')
    pkg_item_info_dict = dict(map(
        lambda i:conv_pkg_info(list(map(
            lambda l:list(map(
                lambda ll:ll.strip(),
                l.split(':'))),
            i.split('\n')))),
        pkg_info_list))
    
    #  provider
    pkg_provider_dict = dict()
    for pkg in pkg_item_info_dict:
        provider_list = list(map(lambda x:x.split('='), pkg_item_info_dict[pkg][1]))
        for provider in provider_list:
            if len(provider) == 1:
                pkg_provider_dict[provider[0]] = ['', pkg]
            else:
                pkg_provider_dict[provider[0]] = [provider[1], pkg]
                
    # 
    for pkg in pkg_item_info_dict:
        for needstr in pkg_item_info_dict[pkg][1]:
            need = needstr.split('=')
            if need[0] in pkg:
                print('pkg ' + need[0])

def get_pkg_depends(pkg):
    query_result = os.popen("env LANG=C pacman -Qi " + pkg + " 2>/dev/null | grep 'Depends On'").read()
    if len(query_result) == 0:
        return
    result = list(map(
        lambda s:s.split('=')[0].split('>')[0].split('<')[0],
        query_result.split(':')[1].split()))
    if 'None' in result:
        result.remove('None')
    return result

def get_pkglist_recursive_needs(pkglist):
    depends_dict = dict()
    result = set()
    query_invalid_result = set()
    
    def add_pkg_recursive_needs(pkglist_):
        for pkg in pkglist_:
            if not pkg in depends_dict:
                new_deps = get_pkg_depends(pkg)
                if new_deps is None:
                    query_invalid_result.add(pkg)
                else:
                    result.add(pkg)
                    depends_dict[pkg] = new_deps
                    add_pkg_recursive_needs(new_deps)


    add_pkg_recursive_needs(pkglist)
    return [result, query_invalid_result]

def get_conf_pkg_set():
    lines = open(conf_file).readlines()
    s_set = set()
    for line in lines:
        pkg = line.strip().split('#', 1)[0]
        if len(pkg) != 0:
            s_set.add(pkg)
    return s_set


if __name__ == '__main__':
    get_system_pkgs()
    #if os.path.exists(conf_file):
    #    print(get_pkglist_recursive_needs({'glibc','wef','xz','w','www'}))
    #else:
    #    print('please edit ' + conf_file)
