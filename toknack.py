#!/usr/bin/env python

from azure.cli.core.application import Configuration


def main(args):
    config = Configuration()
    commands = config.get_command_table()
    keys = sorted(commands.keys())
    tocode = []

    for k in keys:
        if args.prefix and not k.startswith(args.prefix):
            continue

        if args.details:
            print_command_info(commands[k])
        elif args.code:
            tocode.append(commands[k])
        else:
            print(k)
    
    if tocode:
        print_code(tocode)

def print_command_info(command):
    from tabulate import tabulate

    command.load_arguments()

    print('\n{}\n'.format(command.name.upper()))

    attributes = []
    for attr in dir(command):
        if attr.startswith('__'):
            continue

        value = getattr(command, attr)
        if isinstance(value, dict):
            attributes.append({'name': '{}'.format(attr), 'value': ''})
            for k in value:
                attributes.append({'name': '...{}'.format(str(k)), 'value': value[k]})
        else:
            value = str(value)
            attributes.append({'name': attr, 'value': value})
    
    attributes.append({'name': 'X:OPERATION', 'value': command.handler.func_closure[5].cell_contents})

    print(tabulate(attributes, tablefmt='plain'))
    print('<<<<')

def print_code(commands):
    groups = set([c.name.rsplit(' ', 1)[0] for c in commands])
    if len(groups) != 1:
        raise ValueError('More than one group is identified.')

    commands_meta = []
    for c in commands:
        group, name = c.name.rsplit(' ', 1)
        handler_module, handler_func = c.handler.__closure__[5].cell_contents.rsplit('#', 1)
        if handler_module.startswith('azure.cli.command_modules'):
            # this is a custom command, assume the custom type is predefined in the loader
            cmd = KnackCommandMeta(name, is_custom=True, custom_func=handler_func)
            commands_meta.append(cmd)
        else:
            raise NotImplementedError()
    

    print('\n>>>>')
    code = """
    with self.command_group('{}', sdk_placeholder, resource_type=ResourceType.UNKNOWN) as g:
{}
""".format(group, '\n'.join(r.to_code('g', 2) for r in commands_meta))
    print(code)
    print('<<<<')


class KnackCommandMeta(object):
    def __init__(self, name, is_custom=False, custom_func=None):
        self.name = name
        self.is_custom = is_custom
        self.custom_func = custom_func
    
    def to_code(self, group_name, indent=0):
        indentation = ' ' * 4 * indent
        if self.is_custom:
            imple = f"{indentation}{group_name}.custom_command('{self.name}', '{self.custom_func}')"
        else:
            raise NotImplementedError()
        return imple


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('toknack')
    parser.add_argument('--prefix')
    parser.add_argument('--details', action='store_true')
    parser.add_argument('--code', action='store_true')
    args = parser.parse_args()
    main(args)