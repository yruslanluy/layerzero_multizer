import layer0


if __name__ == '__main__':
    print('\nLayerZero multizer 1.5.3 [build 0615] // by Cryptochy Labs\n')
    print('////   https://t.me/cryptochy   ////\n')
    with open('config.txt', 'r') as file:
        configs = file.readlines()

    config = {}
    for x in configs:
        al = x.rstrip().split(' ')
        config[al[0]] = al[2]

    layer0.start(config)
