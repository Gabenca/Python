
###############################################################################
##########################   Ethical disclaimer   #############################
###############################################################################

# In this application, we work with the portal and API of the headhunter.ru company.
# We are very grateful to headhunter.ru company for the beautiful portal 
# and excellently-designed well-documented API, programming with which was a pure pleasure.
# We are aware of the complexity of the development and maintenance of such services 
# and such a business as a whole. We are also fully aware that specialized databases 
# are one of the main assets of the company.
#
# In connection with the foregoing, we should in no case forget that:
#
#      THIS APPLICATION WAS CREATED EXCLUSIVELY FOR EDUCATIONAL PURPOSES
#      AND COMPLETELY EXCLUDES THE POSSIBILITY OF ANY BUSINESS USE.
#
# Also remember that the company itself provides analytical reporting services 
# that you can always use and this will be the best choice.

###############################################################################
####   This is SERVER version, intended for deploying to OS environment!   ####
###############################################################################

#---Imports--------------------------------------------------------------------
#------------------------------------------------------------------------------

# OS API functions:
import os
# Regexp stuff:
import re
# [De]Serializing objects:
import json
# Delay function:
import time
# Excel documents processing:
import pandas
# Native objects store:
import pickle
# Code profiling:
import cProfile
# HTTP requests:
import requests
# Some math:
import statistics
# Some data structures:
import collections

# HTML parser:
from bs4 import BeautifulSoup
# MongoDB connection stuff:
from pymongo import MongoClient
# Preetty progressbar
from tqdm import tqdm

# Some filter stuff:
from laboranalysis.filtervocabulary import vocabulary
# Our credentials:
from laboranalysis.credentials import mongo, store_path


#---Class----------------------------------------------------------------------
#------------------------------------------------------------------------------

class VacancyHandler:
    '''
    ----------------------------------------------------
    Class is designed to collect and analyze information
      about vacancies retrieved from HeadHunter REST API 

    Public methods:

        exclude_by_region(exclude_geo_area)
        include_by_region(include_geo_area)
        unpickle_vacancies(filesystem_store_path)
        analyze()
        pickle_vacancies()
        store_vacancies_to_mongo()
        store_results_to_xlsx()
    ----------------------------------------------------        
    '''

#------------------------------------------------------------------------------
#---Initializations------------------------------------------------------------
#------------------------------------------------------------------------------

    # Base HeadHunter API-url for vacancy retrievement
    api_url = 'https://api.hh.ru/vacancies'

    def __init__(self,
        # Text to be searched in vacancy to establish a match condition
        # Occupation name, in main
        search_criteria,
        # Place in vacancy in which match condition will be established
        search_field='name',
        # Region restriction for vacancy search, for example:
        # Russia(113), Novosibirsk(1202), Moscow(1) region
        geo_areas=['1202',]):
        
        # Text to be searched in vacancy to establish a match condition
        # Occupation name, in main
        self.search_criteria = search_criteria

        # Region restriction for vacancy search, for example:
        # Russia(113), Novosibirsk(1202) region
        self.search_geo_areas = geo_areas

        # HTTP request to API parameters
        self.search_parameters = {
            'text': self.search_criteria,
            ##'salary': average_salary,
            'area': self.search_geo_areas,
            'per_page': 100,
            'page': 0,
            'clusters': 'true',
            'describe_arguments': 'true',
            }

        # Full vacancies batch itself
        self.vacancies = []

        # Names of all vacancies in batch
        self.vacancy_names = None

        # Keyskills (tags) top and all
        self.skills = None
        self.skills_all = None
 
        # Keywords (all english words) top and all
        self.keywords = None
        self.keywords_all = None

        # All subject headings (html 'strongs') from vacancy descriptions
        self.description_sections = None

        # Child elements from all subject headings (html 'strongs')
        self.description_elements_all = None

        # Child elements from top 10 subject headings (html 'strongs')
        self.description_elements = None

        # Child elements from description_sections_top subject headings (html 'strongs')
        self.description_elements_top = None

        # Wordbags formed from self.description_elements
        self.wordbags_all = None
        
        # Wordbags formed from self.description_sections_top
        self.wordbags = None
        
        # Common professional areas in retrieved vacancies
        self.profareas = None
        
        # Specialization areas in retrieved vacancies
        self.profareas_granular = None
        
        # Publication dates
        self.dates = None
        
        # Regions
        self.regions = None
        
        # Required experience
        self.experience = None

        # Employers list with full info: id, vacancies url . . .
        self.employers_full = None
        # Employers list in {name:url} format
        self.employers_brief = None
        
        # Number of unique vacancies among all
        self.unique = None
        
        # HH clusters of vacancies
        self.clusters = None

        # Average, median, modal salaries
        self.salaries = []

        # Average salary
        self.average_salary = 0

        # Median salary
        self.median_salary = 0

        # Modal salary
        self.modal_salary = 0

        # Salary groups
        self.salary_groups = {
            'Менее 20000' : 0,
            '20000-30000' : 0,
            '30000-40000' : 0,
            '40000-50000' : 0,
            '50000-60000' : 0,
            '60000-70000' : 0,
            '70000-90000' : 0,
            'Более 90000' : 0
            }

        self.salaries_by_region = None

        # Top of 'strong's' dictionary corpus,
        # formed from lots of batches of different vacancies
        # retrieved previously
        self.description_sections_top = frozenset({
            'Требования',
            'Обязанности',
            'Условия',
            'Мы предлагаем',
        })
        
        # Search arguments returned by HH server
        self.search_arguments = None

        if search_field:
            self.search_parameters['search_field'] = search_field
        ##if search_area: 
        ##    self.search_parameters['area'] = search_area

        # Determines when the class instance is freshly created
        # and actually does not contain vacancies yet
        self.__initial = True

        # Global path to store pickles and results
        self.store_path = store_path

    def __len__(self):
        return len(self.vacancies)

    def __getitem__(self, position):
        return self.vacancies[position]

    def __repr__(self):
        return (f"Totally {self.__len__()} vacancies on "
        f"'{self.search_parameters.get('text', 'undefined')}' occupation")

#------------------------------------------------------------------------------
#---Retrievers-----------------------------------------------------------------
#------------------------------------------------------------------------------

    # Retrieve vacancies from HH
    #--------------------------------------------------------------------------
    def _vacancies_retriever(self, delay, number):

        brief_vacancies = []
        current_page = 0
        # Vacancies retrievement batch amount limiter (per_page * number)
        if number is not None: 
            pages_count = int(number)
        else:
            pages_count = current_page + 1

        while current_page < pages_count:
            self.search_parameters['page'] = current_page
            raw_response = requests.get(VacancyHandler.api_url,
                                        params = self.search_parameters)
            response = raw_response.json()
            brief_vacancies += response.get('items')
            if number is None:
                pages_count = response.get('pages')
            current_page += 1

        self.clusters = response.get('clusters')

        # Collecting urls which link to full vacancy descriptions
        urls = [vacancy.get('url')
            for vacancy in brief_vacancies]

        # Form a list of full vacancies without request delay
        ##self.vacancies = [requests.get(url).json() for url in tqdm(urls)]
        
        # Form a list of full vacancies with request delay
        for url in urls:
            self.vacancies.append(requests.get(url).json())
            time.sleep(int(delay))

        self.search_arguments = response.get('arguments')

        # Now the class instance already contains actual vacancies
        self.__initial = False

    # Announces general information on the response to the request
    # Asks for confirmation for the full retrievement
    # Start full retrievement, if confirmed
    #--------------------------------------------------------------------------
    def _retrievement_confirmator(self):

        raw_response = requests.get(VacancyHandler.api_url,
                                    params = self.search_parameters)
        response = raw_response.json()
        pages_count = response.get('pages')
        
        vacancies_amount = pages_count*self.search_parameters['per_page']
        occupation = self.search_parameters.get('text')

        print(f"\nThere are {vacancies_amount} vacancies",
              f"on '{occupation}' occupation available on hh.ru",
              f"\n\nRetrieve it now ( [y]es, [n]o ) ?")
        answer = input()
        
        if answer.lower() == 'y':
            print("\nDo you want to get all the vacancies ",
                  "or only part of them ( [a]ll, [p]art ) ?")
            number = None
            answer = input()

            if answer.lower() == 'p':
                print("\nPlease specify desired number ",
                      "of hundreds (e.g. 2 means 200 vacancies)")
                number = input()

            print("\nDo you want to add a delay ",
                  "between requests to api ( [y]es, [n]o ) ?")
            delay = 0
            answer = input()

            if answer.lower() == 'y':
                print("\nPlease specify the delay time in seconds:")
                delay = input()

            print(f"\n\n")
            self._vacancies_retriever(delay, number)

#------------------------------------------------------------------------------
#---Filters--------------------------------------------------------------------
#------------------------------------------------------------------------------

    def exclude_by_region(self, exclude):
        '''Exclude vacancies by 'exclude' criteria from all vacancies batch'''
        self.vacancies = [vacancy
            for vacancy in self.vacancies
                if vacancy.get('area').get('name') != exclude]

    #--------------------------------------------------------------------------
    def include_by_region(self, include):
        '''Include vacancies by 'include' criteria from all vacancies batch'''
        self.vacancies = [vacancy
            for vacancy in self.vacancies
                if vacancy.get('area').get('name') == include]

#------------------------------------------------------------------------------
#---Store----------------------------------------------------------------------
#------------------------------------------------------------------------------

    def pickle_vacancies(self, path=None):
        '''Store object 'vacancies' into file located in "path"'''
        file_name = f"{self.search_parameters.get('text')}.pickle"
        if path is None:
            path = f"{self.store_path}/"
        file_path = path + file_name
        with open(file_path, 'wb') as file:
            pickle.dump(self.vacancies, file)

    #--------------------------------------------------------------------------
    def unpickle_vacancies(self, path):
        '''Restore object 'vacancies' from file located in "path"'''
        with open(path, 'rb') as file:
            self.vacancies += pickle.load(file)
        # Now the class instance already contains actual vacancies
        self.__initial = False

    #--------------------------------------------------------------------------
    def store_vacancies_to_mongo(self):
        '''Store vacancies to MongoDB'''
        # Instantiate MongoDB connection context
        with MongoClient(mongo) as mongodb:
            # Connection to criteria collection of 'hh_vacancies' database
            collection = mongodb.hh_vacancies[self.search_criteria]
            # Put vacancies
            collection.insert_many(self.vacancies)        

#------------------------------------------------------------------------------
#---Results--------------------------------------------------------------------
#------------------------------------------------------------------------------

    def store_results_to_xlsx(self):
        '''Store analysis result into xlsx file
        'search_criteria-vacancies_amount.xlsx'
        located in 'store_path' path'''

        # This function forms xlsx document sheet
        def form_sheet(data, columns, name, a_width, b_width):
            # Defines sheet structure
            sheet = pandas.DataFrame(data, columns=columns)
            # Add sheet to xlsx document
            sheet.to_excel(writer, name, index=False)
            worksheet = writer.sheets[name]
            worksheet.set_column('A:A', a_width)
            worksheet.set_column('B:B', b_width)
            worksheet.conditional_format('A2:A11', {'type': '3_color_scale'})

        # This function forms xlsx document diagrams
        def form_chart(data, name, amount, type, code):
            workbook = writer.book
            worksheet = writer.sheets[name]
            chart = workbook.add_chart({'type': type})
            chart.add_series({
                'categories': f"='{name}'!$A$2:$A${amount}",
                'values':     f"='{name}'!$B$2:$B${amount}",
            })
            if type != 'pie':
                chart.set_x_axis({'name': data[0], 'num_font':  {'rotation': 45}})
                chart.set_y_axis({'name': data[1], 'major_gridlines': {'visible': False}})
                chart.set_legend({'position': 'none'})
            worksheet.insert_chart(code, chart)

        # Xlsx file structure
        table_structure = {
            'Должности': ['Название должности', 'Количество вакансий'],
            'Ключевые навыки': ['Ключевые навыки', 'Вакансий'],
            'Опыт': ['Требуемый опыт', 'Вакансий'],        
            'Технологии': ['Продукты|Технологии', 'Вакансий'],        
            'Работодатели': ['Работодатель', 'Ссылка'],
            'Регионы': ['Регион', 'Вакансий'],
            'Профобласти': ['Профобласть', 'Вакансий'],
            'Специализации': ['Специализация', 'Вакансий'],
            'Группы': ['Диапазон', 'Вакансий'],
            'Зарплата': ['Зарплата', 'Рублей'],
        }
        
        # Xlsx report file path and name
        path = ( f'{self.store_path}/vacancies/'
                 f'{self.search_criteria}-'
                 f'{len(self.vacancies)}.xlsx' )
        
        # Instantiate ExcelWriter context
        with pandas.ExcelWriter(path) as writer:

            try:
                form_sheet( self.vacancy_names, 
                            table_structure['Должности'],
                            'Должности', 60, 25 )
                form_chart( table_structure['Должности'],
                            'Должности', '11', 'column', 'D2' )
            except:
                pass

            try:
                form_sheet( self.skills_all, 
                            table_structure['Ключевые навыки'],
                            'Ключевые навыки', 50, 20 )
                form_chart( table_structure['Ключевые навыки'], 
                            'Ключевые навыки', '11', 'column', 'D2' )
            except:
                form_sheet( ['Не найдено'], 
                            ['Не найдено'], 
                            'Ключевые навыки', 35, 15 )

            try:
                form_sheet( self.keywords_all, 
                            table_structure['Технологии'], 
                            'Технологии', 30, 20 )
                form_chart( table_structure['Технологии'], 
                            'Технологии', '11', 'column', 'D2' )
            except:
                form_sheet( ['Не найдено'], 
                            ['Не найдено'], 
                            'Технологии', 35, 15 )
        
            try:
                form_sheet( self.regions, 
                            table_structure['Регионы'], 
                            'Регионы', 35, 20 )
                form_chart( table_structure['Регионы'], 
                            'Регионы', '11', 'column', 'D2')
            except:
                pass

            try:
                form_sheet( self.experience, 
                            table_structure['Опыт'], 
                            'Опыт', 30, 20 )
                form_chart( table_structure['Опыт'], 
                            'Опыт', '5', 'pie', 'C3' )
            except:
                pass
        
            try:            
                form_sheet( self.employers_brief.items(), 
                            table_structure['Работодатели'], 
                            'Работодатели', 50, 35 )
            except:
                form_sheet( ['Не найдено'], 
                            ['Не найдено'], 
                            'Работодатели', 35, 15)
            
            try:
                form_sheet( self.profareas, 
                            table_structure['Профобласти'], 
                            'Профобласти', 55, 20 )
                form_chart( table_structure['Профобласти'], 
                            'Профобласти', '11', 'column', 'D2' )
            except:
                pass
    
            try:
                form_sheet( self.profareas_granular, 
                            table_structure['Специализации'], 
                            'Специализации', 45, 20 )
                form_chart( table_structure['Специализации'], 
                            'Специализации', '11', 'column', 'D2' )
            except:
                pass
            
            try:
                form_sheet( self.salary_groups.items(), 
                            table_structure['Группы'], 
                            'Зарплатные группы', 25, 20 )
                form_chart( table_structure['Группы'], 
                            'Зарплатные группы', '11', 'column', 'D2' )
            except:
                form_sheet( ['Не найдено'], 
                            ['Не найдено'], 
                            'Зарплатные группы', 35, 15 )

            try:
                form_sheet( self.salaries, 
                            table_structure['Зарплата'], 
                            'Зарплата', 25, 20 )
            except:
                form_sheet( ['Не найдено'], 
                            ['Не найдено'], 
                            'Зарплата', 35, 15 )

            for criteria in vocabulary['Знания']:
                try:
                    form_sheet(set(self._by_word_extractor(criteria)),
                            [criteria.capitalize()],
                            criteria.capitalize(), 100, 30)
                except:
                    pass

            for criteria in self.description_elements_top:
                try:
                    form_sheet(set(self.description_elements_top.get(criteria)),
                            [criteria.capitalize()],
                            criteria.capitalize(), 100, 30)
                except:
                    pass

            try:
                form_sheet( self.wordbags_all, 
                            ['Слово', 'Вхождений'], 
                            'Мешок слов', 25, 20 )
            except:
                pass

#------------------------------------------------------------------------------
#---Analyze--------------------------------------------------------------------
#------------------------------------------------------------------------------

    # Call all analyze methods                        
    def analyze(self):

        # If class instance doesn't contains actual vacancies
        if self.__initial:
            # Retrieve it
            self._vacancies_retriever(delay=10, number=None)
            ##self._retrievement_confirmator()
        self._duplicate_vacancies_remover()
        self._skills_collector()
        self._experience_collector()
        self._prof_areas_collector()
        self._creation_dates_collector()
        self._vacancy_names_collector()
        self._regions_collector()
        self._keywords_extractor()
        self._description_elements_extractor()
        self._description_sections_extractor()
        self._wordbags_extractor()
        self._unique_counter()
        self._salary_calculator()
        self._employers_collector()

#------------------------------------------------------------------------------
#---Collectors-----------------------------------------------------------------
#------------------------------------------------------------------------------

    # Collect key skills
    #--------------------------------------------------------------------------
    def _skills_collector(self):

        raw_key_skills = [vacancy.get('key_skills')
            for vacancy in self.vacancies]

        # Cleaning skills
        mixed_key_skills = [key_skill.get('name')
            for item in raw_key_skills
                for key_skill in item]

        # Forms {key_skill : number of entries}
        key_skills_counted = {skill : mixed_key_skills.count(skill)
            for skill in mixed_key_skills}

        # Sort by number of entries
        self.skills_all = sorted(key_skills_counted.items(),
                                 key=lambda x: x[1],
                                 reverse=True)
        
        self.skills = self.skills_all[0:100]

    # Collect required work experience from vacancies
    #--------------------------------------------------------------------------
    def _experience_collector(self):

        raw_experience = [full_vacancy.get('experience').get('name')
            for full_vacancy in self.vacancies]

        # Forms {experience : number of entries}
        experience = {exp : raw_experience.count(exp)
            for exp in raw_experience}

        # Sort by number of entries
        self.experience = sorted(experience.items(),
                                 key=lambda x: x[1],
                                 reverse=True)

    # Collect vacancy names
    #--------------------------------------------------------------------------
    def _vacancy_names_collector(self):

        vacancy_names = [vacancy.get('name').lower()
            for vacancy in self.vacancies]

        # Forms {vacancy name : number of entries}
        vacancy_names_counted = {name.capitalize() : vacancy_names.count(name)
            for name in vacancy_names}

        # Sort by number of entries
        self.vacancy_names = sorted(vacancy_names_counted.items(),
                                    key=lambda x: x[1],
                                    reverse=True)

    # Collect specialization areas from vacancies
    #--------------------------------------------------------------------------
    def _prof_areas_collector(self):

        raw_specializations = [full_vacancy.get('specializations')
            for full_vacancy in self.vacancies]
        
        specializations = [vacancy_specializations
            for vacancy_specializations_list in raw_specializations
                for vacancy_specializations in vacancy_specializations_list]
        
        profareas = [key['profarea_name']
            for key in specializations]
        
        profareas_granular = [key['name']
            for key in specializations]
        
        # Forms {profarea : number of entries}
        profareas_counted = {profarea : profareas.count(profarea)
            for profarea in profareas}
        
        # Forms {granular profarea : number of entries}        
        profareas_granular_counted = {profarea : profareas_granular.count(profarea)
            for profarea in profareas_granular}

        # Sort by number of entries
        self.profareas = sorted(profareas_counted.items(),
                                key=lambda x: x[1],
                                reverse=True)

        # Sort by number of entries        
        self.profareas_granular = sorted(profareas_granular_counted.items(),
                                         key=lambda x: x[1],
                                         reverse=True)
    
    # Collect creation dates from vacancies
    #--------------------------------------------------------------------------
    def _creation_dates_collector(self):

        raw_create_dates = [vacancy.get('created_at')
            for vacancy in self.vacancies]
        
        # Sort by date of publication
        self.dates = sorted({date : raw_create_dates.count(date)
            for date in raw_create_dates})
    
    # Collect employers
    #--------------------------------------------------------------------------
    def _employers_collector(self):

        self.employers_full = [vacancy.get('employer')
            for vacancy in self.vacancies]

        self.employers_brief = {vacancy.get('employer').get('name') :
                                vacancy.get('employer').get('alternate_url')
            for vacancy in self.vacancies}

    # Collect regions
    #--------------------------------------------------------------------------
    def _regions_collector(self):

        regions = [vacancy.get('area').get('name')
            for vacancy in self.vacancies]

        # Forms {regions : number of entries}
        regions_counted = {region : regions.count(region)
            for region in regions}
        
        # Sort by number of entries
        self.regions = sorted(regions_counted.items(),
                              key=lambda x: x[1],
                              reverse=True)

#------------------------------------------------------------------------------
#---Extractors-----------------------------------------------------------------
#------------------------------------------------------------------------------

    # Wordbags formed from self.description_sections_top, which in turn is
    # Top of 'strong's' dictionary formed from lots of batches of different vacancies
    #--------------------------------------------------------------------------
    def _wordbags_extractor(self):

        def extract_by_criteria(criteria):
            
            if self.description_elements.get(criteria):
                clear_strings = [re.sub("[^А-Яа-я0-9-.\s]", "",
                                        describe_string.lower().strip().strip('.'))
                    for describe_string in self.description_elements.get(criteria)]

                unique_clear_set = set(clear_strings)
                unique_strings = [str(string)
                    for string in unique_clear_set]

                ##unique_strings = sorted(unique_strings, key=len)
                bags_words = [collections.Counter(re.findall(r'\w+', string))
                    for string in unique_strings]

                bag_words = sum(bags_words, collections.Counter())
                sorted_bag = sorted(bag_words.items(), key=lambda x: x[1], reverse=True)
                result = [word for word in sorted_bag
                    if len(word[0]) > 4]

                return result
        
        self.wordbags = {criteria : extract_by_criteria(criteria)
            for criteria in self.description_sections_top}
        
        all_words_in_string = ' '.join(self.description_elements_all)    
        bags_words = collections.Counter(re.findall(r'\w+', all_words_in_string))
        self.wordbags_all = sorted(bags_words.items(),
                                   key=lambda x: x[1],
                                   reverse=True)

    # Extract all english words from vacancy desriptions
    #--------------------------------------------------------------------------
    def _keywords_extractor(self):

        # Texts list from vacancy descriptions
        descriptions = [BeautifulSoup(vacancy.get('description'), 'html.parser').get_text()
            for vacancy in self.vacancies]

        # Extract english words
        raw_eng_extraxtions = [re.sub("[^A-Za-z]", " ", description.strip())
            for description in descriptions]
        
        # Clearing
        raw_eng_words = [raw_eng_extraxtion.split('  ')
            for raw_eng_extraxtion in raw_eng_extraxtions]
        
        eng_words = [words.strip()
            for raw_eng_word in raw_eng_words
                for words in raw_eng_word
                    if words != '']
        
        clear_eng_words = list(filter(None, eng_words))
        eng_words_mixed = {word : clear_eng_words.count(word)
            for word in clear_eng_words}

        # Sorted by number of entries
        self.keywords_all = sorted(eng_words_mixed.items(),
                                   key=lambda x: x[1],
                                   reverse=True)
        self.keywords = self.keywords_all[0:100]

    # Extract child elements from all subject headings (html 'strongs')
    #--------------------------------------------------------------------------
    def _description_elements_extractor(self):

        # bs4.BeautifulSoup objects list formed from vacancy descriptions
        vacancy_descriptions = [BeautifulSoup(vacancy.get('description'), 'html.parser')
            for vacancy in self.vacancies]
        
        p_tags = [p.text.strip().lower()
            for soup in vacancy_descriptions
                for p in soup.find_all('p')]

        li_tags = [li.text.strip().lower()
            for soup in vacancy_descriptions
                for li in soup.find_all('li')]
        
        self.description_elements_all = list(set(p_tags + li_tags))
    
    # Extract multiple different things from vacancy description bodies
    #--------------------------------------------------------------------------
    def _description_sections_extractor(self):

        # bs4.BeautifulSoup objects list formed from vacancy descriptions
        description_soups = [BeautifulSoup(vacancy.get('description'), 'html.parser')
            for vacancy in self.vacancies]
        
        # Vacancy descriptions sections list grouped by vacancy framed into <strong> tags
        strong_soups = [description_soup.findAll('strong')
            for description_soup in description_soups]

        # All vacancy descriptions sections from all vacancies in common list
        strongs = [strong.text
            for strong_soup in strong_soups
                for strong in strong_soup]

        # Clearing
        clear_strongs = [re.sub("[^А-Яа-я\s]", "", strong.strip())
            for strong in strongs]

        clear_strongs = list(filter(None, clear_strongs))
        clear_strongs = list(filter(lambda x: x!=' ', clear_strongs))

        ##self.description_sections = clear_strongs

        # Forms {strong : number of entries}
        strongs_counted = {strong : clear_strongs.count(strong)
            for strong in clear_strongs}

        # Sort by number of entries
        sorted_strongs = sorted(strongs_counted.items(),
                                key=lambda x: x[1],
                                reverse=True)
        
        self.description_sections = sorted([strong[0]
            for strong in sorted_strongs], key=len, reverse=True)
        
        strong_top = [strong[0]
            for strong in sorted_strongs[:10]]

        self.description_elements = {key: []
            for key in strong_top}

        self.description_elements_top = {key: []
            for key in self.description_sections_top}

        for description in description_soups:
            strongs = description.findAll('strong')
            for strong in strongs:
                for top in strong_top:
                    if strong.get_text().count(top):
                    ##if len(strong.findNext().findAll('li')) > 0:
                        try:
                            self.description_elements[top] += [item.text
                                for item in strong.findNext().findAll('li')]
                        except AttributeError:
                            pass
                
                for top in self.description_sections_top:
                    if strong.get_text().count(top):
                    ##if len(strong.findNext().findAll('li')) > 0:
                        try:
                            # Suffix '.lstrip().capitalize()' clarifies but slows down
                            self.description_elements_top[top] += [item.text.lstrip().capitalize()
                                for item in strong.findNext().findAll('li')]
                        except AttributeError:
                            pass
       
    # Get python list of list 'description_sections_top'
    # filtered by custom 'filter_vocabulary' key
    #--------------------------------------------------------------------------
    # Clear, but slow version
    def _by_word_extractor(self, criteria):

        result = list()   

        for element in self.description_elements_all:
            if criteria in element:
                if element:
                    while element[0].isalpha() == False:
                        element = element.lstrip(element[0])
                        if not element:
                            break
                    result.append(element.capitalize())
        
        return sorted(result, key=len)
    #--------------------------------------------------------------------------
    # Dirty, but fast version
    ##def _by_word_extractor(self, criteria):
    ##    result = [element
    ##        for element in self.description_elements_all
    ##            if criteria in element]
    ##    return sorted(result, key=len)

#------------------------------------------------------------------------------
#---Calculators----------------------------------------------------------------
#------------------------------------------------------------------------------

    # Calculate average, median, modal salaries
    # and group salaries into number of clusters
    #--------------------------------------------------------------------------
    def _salary_calculator(self):
        
        def _get_salary_group(salary):
            return {
                salary < 20000: 'Менее 20000',
                20000 <= salary < 30000: '20000-30000',
                30000 <= salary < 40000: '30000-40000',
                40000 <= salary < 50000: '40000-50000',
                50000 <= salary < 60000: '50000-60000',
                60000 <= salary < 70000: '60000-70000',
                70000 <= salary < 90000: '70000-90000',
                90000 <= salary: 'Более 90000'
            }[True]
        
        sum = total = 0
        salary_all = []
    
        regions = [region[0] for region in self.regions]
    
        region_salary_dict = {'average_salary': 0,
                              'median_salary': 0,
                              'modal_salary': 0,
                              'sum': 0,
                              'total': 0,
                              'salary_all': [],
                            }

        self.salaries_by_region = {region: region_salary_dict
            for region in regions}

        for vacancy in self.vacancies:

            region = vacancy.get('area').get('name')

            if vacancy.get('salary'):
                salary = dict(vacancy['salary'])
                if salary.get('currency') == 'RUR':
                    if salary.get('gross'):
                        if salary.get('from'):
                            salary['from'] = salary['from'] * 0.87
                        if salary.get('to'):
                            salary['to'] = salary['to'] * 0.87
                    if salary.get('from'):
                        self.salaries_by_region[region]['sum'] += salary.get('from')
                        self.salaries_by_region[region]['total'] += 1
                        self.salaries_by_region[region]['salary_all'].append(salary.get('from'))
                        self.salary_groups[_get_salary_group(int(salary.get('from')))] += 1
                        salary_all.append(salary.get('from'))
                        sum += salary.get('from')
                        total += 1
                    if salary.get('to'):
                        self.salaries_by_region[region]['sum'] += salary.get('to')
                        self.salaries_by_region[region]['total'] += 1
                        self.salaries_by_region[region]['salary_all'].append(salary.get('to'))                       
                        self.salary_groups[_get_salary_group(int(salary.get('to')))] += 1
                        salary_all.append(salary.get('to'))
                        sum += salary.get('to')
                        total += 1
        
        self.median_salary = statistics.median(salary_all)
        
        if total > 0:
            self.average_salary = round(sum/total)

        for region in regions:
            self.salaries_by_region[region]['median_salary'] = \
                statistics.median(self.salaries_by_region[region]['salary_all'])

            if self.salaries_by_region[region]['total'] > 0:
                self.salaries_by_region[region]['average_salary'] = \
                    round(self.salaries_by_region[region]['sum'] \
                        / self.salaries_by_region[region]['total'])
        
        # Calculate modal salary
        for group, salary in self.salary_groups.items():
            if salary == max(self.salary_groups.values()):
                self.modal_salary = group

        self.salaries = [('Средняя', self.average_salary),
                         ('Медиана', self.median_salary),
                         ('Модальная', self.modal_salary)
            ]

#------------------------------------------------------------------------------
#---Misc-----------------------------------------------------------------------
#------------------------------------------------------------------------------

    # Remove duplicates in vacancies list
    #--------------------------------------------------------------------------
    def _duplicate_vacancies_remover(self):

        unique_vacancies = []

        for vacancy in self.vacancies:
            if vacancy not in unique_vacancies:
                unique_vacancies.append(vacancy)

        self.vacancies = unique_vacancies

    # Count unique vacancies in vacancies list
    #--------------------------------------------------------------------------
    def _unique_counter(self):
        self.unique = len({vacancy.get('id')
            for vacancy in self.vacancies})


#---Main-----------------------------------------------------------------------
#------------------------------------------------------------------------------

if __name__ == "__main__":

    vacancies = VacancyHandler('Системный администратор')
    pickled_vacancies = (f"{store_path}/SA.pickle")
    vacancies.unpickle_vacancies(pickled_vacancies)
    vacancies.analyze()
    vacancies.store_results_to_xlsx()
