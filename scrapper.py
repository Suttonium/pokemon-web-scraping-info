import cv2
import numpy as np
import urllib.request
import time
from pathlib import Path
from bs4 import BeautifulSoup


def safe_str(obj):
    try:
        return str(obj)
    except UnicodeEncodeError:
        return obj.encode('ascii', 'ignore').decode('ascii')


def get_pokemon_com_images(start=1, end=810):
    """
    1) run the program through the terminal using the following command
        - python scrapper.py
    2) if the following error occurs, follow the steps below:
        - <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer
        - certificate (_ssl.c:1051)>
    3) Navigate to your python 3.x folder and double click the 'Install Certificates.command' file
    4) rerun the program

    :return: void
    """
    img_path = str(Path().absolute()) + '/images/'
    start_time = time.time()
    if start < 1 or end < 1:
        raise Exception('The starting and ending indexes must be positive integers.')
    if start < end:
        for i in range(start, end):
            try:
                url = 'https://assets.pokemon.com/assets/cms2/img/pokedex/detail/' + '{:03d}'.format(i) + '.png'
                request = urllib.request.Request(url)
                response = urllib.request.urlopen(request)
                binary_str = response.read()
                byte_array = bytearray(binary_str)
                numpy_array = np.asarray(byte_array, dtype='uint8')
                image = cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)
                cv2.imwrite(img_path + '{:04d}'.format(i) + '.png', image)
                print('Saved ' + '{:04d}'.format(i) + '.png')
            except Exception as e:
                print(str(e))
    else:
        raise Exception('The starting Pokedex index must be less than the ending Pokedex index.')

    end_time = time.time()
    print('Done')
    print('Time taken: ' + str(end_time - start_time) + 'sec')


def convert_pokemon_names_to_list_constant():
    """
    Using the included pokemon.txt file, this function will create a constants.py file and add the included
    pokemon_names list constant to the file.
    :return: void
    """
    file = open('pokemon.txt', 'r')
    with open('constants.py', 'w') as output_file:
        output_file.write('POKEMON_NAMES = [')
        for line in file:
            line = line.rstrip()
            output_file.write('\'' + line + '\',')
        output_file.write(']')


def get_pokemon_names(file='pokemon.txt') -> list:
    """
    iterate through pokemon.txt and parse names correctly to prepare for data scraping.
    :return: names  -> a list containing the parsed and altered names of every pokemon
    """
    file = open(file, 'r')
    names = []
    for i, line in enumerate(file):
        line = line.rstrip()  # strip whitespace
        if i == 28 or i == 31:
            line = line[:-1]  # remove male or female special character
            if i == 28:
                line = line + '-female'  # special case for female nidoran
            if i == 31:
                line = line + '-male'  # special case for male nidoran
        if line[-1:] == '.':
            line = line.replace(' ', '-').replace('.', '')  # special case for Mime Jr.
        else:
            line = line.replace('.', '-').replace(' ', '') if '.' in line else line
            line = line.replace(' ', '-') if ' ' in line else line
            line = line.replace(':', '') if ":" in line else line
            line = line.replace(safe_str(u'\u2019'), '') if safe_str(u'\u2019') in line else line
            line = line.replace('é', 'e') if 'é' in line else line
        names.append(line)
    return names


def scrape_pokemon_com_info_to_json(file='pokemon.json') -> bool:
    names = get_pokemon_names()
    with open(file, 'w') as json_file:
        json_file.write("{\n\t\"pokemon\": [")
        for i, poke in enumerate(names):
            try:
                print(poke)
                url = 'https://www.pokemon.com/us/pokedex/' + '{0}'.format(poke)
                request = urllib.request.Request(url)
                response = urllib.request.urlopen(request)
                binary_str = response.read()
                soup = BeautifulSoup(binary_str, 'html.parser')

                id_number = soup.findAll('span', {'class': 'pokemon-number'})[2].string

                if id_number != "#720":  # the html for Hoopa contains weird ASCII characters for some reason
                    description = soup.find('meta', property='og:description')['content'].replace('\n', ' ').replace(
                        '"',
                        '')
                else:
                    description = parse_tags(soup.find('p', {'class': 'version-x'}))

                height_list = soup.findAll('span', {'class': 'attribute-value'})[0].string.replace("'", 'ft.') \
                    .replace('"', 'in.').split(' ')
                height_list[1] = height_list[1][1:] if int(height_list[1][0]) == 0 else height_list[1]
                height = height_list[0] + ' ' + height_list[1]
                weight = soup.findAll('span', {'class': 'attribute-value'})[1].string
                category = soup.findAll('span', {'class': 'attribute-value'})[3].string + ' Pokemon'
                abilities = [li.find('span', {'class': 'attribute-value'}).string for li in
                             soup.find('ul', {'class': 'attribute-list'}).findAll('li')]
                types = [li.find('a').string for li in soup.find('div', {'class': 'dtm-type'}).find('ul').findAll('li')]

                if soup.find('li', {'class': 'background-color-noweakness first'}) is not None:  # for no weakness cases
                    weaknesses = ['None']
                else:
                    weaknesses = [li.find('a').find('span').contents[0].string.rstrip() for li in
                                  soup.find('div', {'class': 'dtm-weaknesses'}).find('ul').findAll('li')]

                evolution_tree = [element.contents[0].string.rstrip().replace('\n', '').replace(' ', '') for element
                                  in soup.findAll('h3', {'class': 'match'})]
                json_file.write(
                    "\n\t{\n\t\t\"id\" : " + str(i + 1) + ',\n\t\t\"num\": ' + "\"" + id_number + "\"" +
                    ',\n\t\t\"name\": ' + '\"' + poke + '\",\n\t\t\"img\": ' + '\"' + img_url(id_number) +
                    '\",\n\t\t\"description\": ' + '\"' + description +
                    '\",\n\t\t\"height\": ' + '\"' + height + '\",\n\t\t\"weight\": ' + '\"' + weight +
                    '\",\n\t\t\"category\": ' + '\"' + category + '\",\n\t\t\"abilities\": ' + '[\n\t\t\t' +
                    ''.join(["\"" + ability + "\"" + ",\n\t\t\t" if abilities.index(ability) != len(
                        abilities) - 1 else "\"" + ability + "\"" for
                             ability in abilities]) + '\n\t\t],\n\t\t\"types\": ' + '[\n\t\t' +
                    ''.join(["\t\"" + _type + "\"" + ",\n\t\t\t" if types.index(_type) != len(
                        types) - 1 else "\t\"" + _type + "\"" for
                             _type in types]) + '\n\t\t],\n\t\t\"weaknesses\": ' + '[\n\t\t' +
                    ''.join(["\t\"" + weakness + "\"" + ",\n\t\t" if weaknesses.index(weakness) != len(
                        weaknesses) - 1 else "\t\"" + weakness + "\"" for
                             weakness in weaknesses]) + '\n\t\t' + (
                        '],\n\t\t' if len(evolution_tree) > 1 else ']\t\t') + next_evolution(poke, evolution_tree))
                json_file.write("\n\t}") if names.index(poke) == len(names) - 1 else json_file.write("\n\t},")
            except Exception as e:
                print(str(e))
                return False
        json_file.write("\n]\n}")
        return True


def parse_tags(tag) -> str:
    opening_tag_ending_index = str(tag).find('>')
    tag_text = str(tag)[opening_tag_ending_index + 1:]
    closing_tag_starting_index = tag_text.find('<')
    tag_text = tag_text[:closing_tag_starting_index].replace('\r', '').replace('\n', ' ').strip()
    return tag_text


def img_url(id_number) -> str:
    """
    format url for img json tag
    :param id_number: the scraped id number in #XXX format
    :return: the formatted url for the needed image
    """
    return 'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{0}.png'.format(id_number[1:])


def next_evolution(poke, tree) -> str:
    evolutions = []
    for branch in tree:
        if poke != branch:
            evolutions.append(branch)

    return '\"evolution_tree\": [' + ''.join([
        "\n\t\t{\n\t\t\t\"name\": \"" + branch + '\"' + ('\n\t\t},\t\t' if evolutions.index(
            branch) != len(evolutions) - 1 else '\n\t\t}') for branch in
        evolutions]) + ']' if len(tree) > 1 else ''


if __name__ == '__main__':
    scrape_pokemon_com_info_to_json()
