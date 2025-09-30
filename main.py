#Mrk 15:30
import pathlib, re, logging.config, logging
from typing import Generator, Match, Dict, Any, List
from enum import Enum
from datetime import datetime, time
from re import Pattern
from logging import Logger
from pathlib import Path

#
#GENERIC FUNCTIONS
#

def str_to_date(input_str: str) -> datetime:
    """
    Takes in input a string at that format : 2012.12.31
    and converts it in a datetime type
    """
    date_parts = [int(date_part) for date_part in input_str.split('.')]
    if len(date_parts) == 3:
        year, month, day = date_parts
        return datetime(year,month, day)
    else:
        raise ValueError('YYYY.MM.DD')

def str_to_time(input_str: str) -> time:
    """
    Takes in input a string at that format : 23:01:03
    and converts it in a time type
    """
    time_parts = [int(time_part) for time_part in input_str.split(':')]
    if len(time_parts) == 3:
        hour, min, sec = time_parts
        return time(hour,min,sec)
    else:
        raise ValueError('Date string must have format HH:MM:SS')

#
#EXCEPTIONS
#
class PgnParserException(BaseException):
    """
    Inner & non-interrupting exceptions used by the parser to
    feed the logger
    """
    pass

#
#Data Class
#

class ChessGame():
    """
    Representation of the chess game, takes a dict as input
    the dict must contain the attributes exact name and their
    associated value. At init, the type annotations are parsed to type check
    the attributes. If extra keys are provided input, they will be automatically
    discarded. 
    """
    event       :str
    site        :str
    white       :str
    black       :str
    result      :str
    eco         :str
    opening     :str
    timecontrol :str
    termination :str
    moves       :str
    utcdate     :datetime
    utctime     :time
    whiteelo    :int
    blackelo    :int
    
    def __init__(self, input_dict:Dict[str, Any]) -> None:
        value: Any

        for attr, type in self.__annotations__.items():
            value = input_dict.get(attr, None)
            if isinstance(value, type):
                self.__setattr__(attr, value)
            elif value is None:
                raise PgnParserException(f'Attribute "{attr}" not found')
            else:
                try:
                    #specific type convertion for attr typed to datetime / time
                    if type is datetime:
                        value = str_to_date(value)
                    elif type is time:
                        value = str_to_time(value)
                    #default conversion using type variable
                    else:
                        value = type(value)
                    
                    self.__setattr__(attr, value)
                except Exception as e :
                    raise PgnParserException(f'Unable to cast " {value}"  to {type.__qualname__} for attribute "{attr}"')
                
    def __repr__(self) -> str:
        params_list:List[str] = []
        for attr, value in self.__dict__.items():
            if type(value) is str:
                params_list.append(f'{attr}="{value}"')
            else:
                params_list.append(f'{attr}={value}')

        return f'{type(self).__qualname__}({', '.join(params_list)})'    
    
    def __str__(self) -> str:
        params_list:List[str] = []
        max_value_display_size:int = 15

        for attr, value in self.__dict__.items():
            if type(value) is str:
                if len(value) > 15:
                    value = f'{value[:max_value_display_size]}...'
                params_list.append(f'{attr}="{value}"')
            else:
                params_list.append(f'{attr}={value}')

        return f'{type(self).__qualname__}({', '.join(params_list)})'    

#
#Main engine
#

class DebugMode(Enum):
    VERBOSE = 'verbose'
    SILENT  = 'silent'
    DEBUG   = 'debug'

class PgnParser():
    """
    inputs:
        file_name: full path of the plain/txt file containing the PGN data
        buffer_size: (in bytes) size of the chunks
        debug_mode: boolean used to enable or not the verbose mode

    The PgnParser can parse huge PGN files to extract chess games from the open lichess database
    https://database.lichess.org/

    Note: This is NOT designed to support every PGN possible format, only those provided by lichess database.
    """
    buffer_size     :int
    file_name       :str
    pgn_pattern     :Pattern 
    logger          :Logger
    debug_mode      :DebugMode
    qualname        :str
    chunk_count     :int
    chunk_pos       :Dict[str, int]
    max_data_size   :int
    current_line    :int
    current_dir     :Path
    pgn_abspath     :Path

    LINESEP         :str = '\n'
    PGN_DELIM       :str = '\n\n'
    ENCODING        :str = 'utf-8'

    def __init__(self, file_name: str,buffer_size: int=1024, debug_mode:DebugMode = DebugMode.SILENT) -> None:      
        self.qualname       = type(self).__qualname__ 
        self.current_dir    = Path(__file__).parent.resolve()
        self.debug_mode     = debug_mode

        self.chunk_count    = 0
        self.chunk_pos      = {'start':1, 'end':1}
        self.buffer_size    = buffer_size
        self.max_data_size  = buffer_size * 2 #Arbitrary
        self.current_line   = 1

        self.file_name      = file_name
        self.pgn_abspath    = Path(self.current_dir, file_name)

        self.logger = self.init_logger()
        self.logger.debug('Logger initated.')

        self.pgn_pattern = re.compile(
            r'(\[[^\]]+\s"[^"]+"\]\n?)+'               #Headers like [blablabla "blablabl"]\n -> x times
            r'\n{2}'                                   #Delimiter between PGN headers and actual moves
            r'.*(1-0|0-1|1/2-1/2)'                     #Anything until you reach the result of the game
            ) 

        if not pathlib.Path(self.pgn_abspath).exists():
            raise FileNotFoundError(f"The provided file name doesn't exist: {self.pgn_abspath}")
        
    def init_logger(self) -> Logger:
        handlers: List['str']   = []
        log_abspath:str         = str(Path(self.current_dir,f'Logs/{self.qualname}.log'))

        if self.debug_mode == DebugMode.DEBUG:
            logger_level = 'DEBUG'
            handlers     = ['console','file']
        elif self.debug_mode == DebugMode.SILENT:
            logger_level = 'ERROR'
            handlers     = ['file']
        elif self.debug_mode == DebugMode.VERBOSE:
            logger_level = 'INFO'
            handlers     = ['console','file']
        else:
            raise ValueError('Unknown DEBUG MODE.')
        
        log_config = {
            'version':1,
            'disable_existing_loggers': True,
            'formatters':{
                'standard':{
                    'format':'[%(asctime)s] [%(levelname)s] - [%(name)s] : %(message)s'
                }
            },
            'handlers':{
                'console':{
                    'level':'DEBUG',
                    'formatter':'standard',
                    'class':'logging.StreamHandler',
                    'stream':'ext://sys.stdout'
                },
                'file':{
                    'level':'ERROR',
                    'formatter':'standard',
                    'class':'logging.FileHandler',
                    'filename':log_abspath,
                    'encoding':self.ENCODING,
                    'mode':'a'
                }
            },
            'loggers': {
                self.qualname: {
                    'handlers':handlers,
                    'level': logger_level,
                    'propagate': False
                }
            }
        }

        logging.config.dictConfig(log_config)
        return logging.getLogger(self.qualname)

    def parse_games(self) -> Generator[ChessGame]:
        """
        File parser, that will split the file in chunks which the size is based on the buffer value of the instance
        """
        match: Match
        leftover: str = ''
        match_pos: int = 0
        valid_games_count: int = 0
        invalid_games_count: int = 0
        
        self.logger.info(f'Opening the file {self.file_name} read-only. Chunk size={self.buffer_size}')
        with open(self.pgn_abspath,'r',encoding=self.ENCODING) as f:
            while(chunk := f.read(self.buffer_size)) != '':
                self.chunk_pos['start'] = self.chunk_pos['end']
                self.chunk_pos['end']   = self.chunk_pos['start'] + chunk.count(self.LINESEP)
                
                data = leftover + chunk
                self.current_line = self.chunk_pos['start'] - leftover.count(self.LINESEP) 

                self.logger.debug(f'reading chunk #{self.chunk_count} | line {self.current_line} | {self.chunk_count * self.buffer_size / 1024} Mbytes parsed')
                for match in re.finditer(self.pgn_pattern, data):
                    try:
                        yield self.pgn_to_chessgame(match.group())
                        valid_games_count += 1
                    except PgnParserException as e:
                        processed_lines     = data[:match.start()].count(self.LINESEP)
                        match_pos           = self.current_line + processed_lines 
                        self.logger.error(f'Discarding game :{e} | PGN @line {match_pos}')
                        invalid_games_count += 1

                if match:
                    leftover = data[match.end():] #last match position till the end of the chunk
                else:
                    if len(data)+len(leftover) > self.max_data_size:
                        raise Exception(f'Increase the size of the buffer. Current size : {self.buffer_size}')

                    leftover = data

                self.chunk_count += 1

            self.logger.info(f'Closing {self.file_name}. Valid games count: {valid_games_count} | Invalid games count: {invalid_games_count} ')
    
    def pgn_to_chessgame(self, pgn_string: str) -> ChessGame:
        """
        Takes as input the result of the PGN regex to perform
        some string manipulation and will convert it to a dict that will 
        be passed to the ChessGame class 
        """
        pgn_dict: Dict[str, str]= {}
        split_pgn: list[str]    = pgn_string.split(self.PGN_DELIM)
        headers: str            = split_pgn[0]
        moves: str              = split_pgn[1]

        if(len(split_pgn) != 2):
            raise PgnParserException(f'The pgn must contain 2 parts seperated by \\n\\n')

        for header in headers.split(self.LINESEP):
            self.logger.debug(f'Parsing header : {header}')
            split_header = header[1:-1].split(' "')  #[1:-1] to trim [ & ]
            if (not header.startswith('[') or not header.endswith(']')) or len(split_header) != 2:
                raise PgnParserException(f'Malformed header : {header}')
        
            header_name     = split_header[0]
            header_value    = split_header[1].rstrip('"') #striping " from the string
            pgn_dict.update({header_name.lower(): header_value}) #tolower() to have the exact match of attr names in the ChessGame class
        
        pgn_dict.update({'moves':moves})
        return ChessGame(pgn_dict)
    
if __name__ == '__main__':
    pgnParser = PgnParser(file_name="Pgn/lichess_db_standard_rated_2013-01.pgn",
                buffer_size=200_000,
                debug_mode=DebugMode.VERBOSE)

    for game in pgnParser.parse_games():
        print(game)