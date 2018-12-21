grammar record_grammar;

value:      object
    |       array
    |       string
    |       number
    |       TRUE
    |       FALSE
    |       NULL
    ;
object:     OPEN_BRACE WS CLOSE_BRACE
    |       OPEN_BRACE members CLOSE_BRACE
    ;
members:    member
    |       member COMMA members
    ;
member:     WS string WS COLON element
    ;
array:      OPEN_BRACKET WS CLOSE_BRACKET
    |       OPEN_BRACKET elements CLOSE_BRACKET
    ;
elements:   element
    |       element COMMA elements
    ;
element:    WS value WS
    ;
string:     DBL_QUOTE characters? DBL_QUOTE
    ;
characters: character characters?
    ;
character:  ~(DBL_QUOTE | BACKSLASH)
    |       BACKSLASH escape
    ;
escape:     ESC_CHARS
    |       UNICODE_PFX HEX HEX HEX HEX
    ;
number:     INT FRAC? EXP?
    ;

TRUE:           'true';
FALSE:          'false';
NULL:           'null';
OPEN_BRACE:     '{';
CLOSE_BRACE:    '}';
COMMA:          ',';
COLON:          ':';
OPEN_BRACKET:   '[';
CLOSE_BRACKET:  ']';
DBL_QUOTE:      '"';
BACKSLASH:      '\\';
ESC_CHARS:      ["\\/bnrt];
UNICODE_PFX:    'u';
HEX:            [0-9A-Fa-f];
INT:            [+\-]? [1-9] [0-9]*;
FRAC:           '.' [0-9]+;
EXP:            [Ee] [+\-] [0-9]+;
WS:             [ \n\r\t];