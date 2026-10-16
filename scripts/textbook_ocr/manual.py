# 人工核对：清洗后的词头 -> 正确词头；None = 删掉（释义残行、标题、识别垃圾）
FIX = {
 'nergnbour':'neighbour','Eaward':'Edward','add iron.&':None,'thousandsof':'thousands of','Tdentify':'identify',
 'l.& it':None,'it.&':None,'Ut.&':None,'Liqura':'liquid','moustache lespecrally US mustache':'moustache',
 'Qlarrnoea':'diarrhoea','denyaration':'dehydration','overwnetming puma welmtg':'overwhelming','as far asiknow':'as far as I know',
 'raalation':'radiation','Giotto di condone':'Giotto di Bondone','Glaays Ctaffern':'Gladys Claffern','Sclence':'science',
 'Ciouay':'cloudy','wongeriul':'wonderful','Ightning':'lightning','anybody fenibodil':'anybody','yourselves selvzl':'yourselves',
 'lonely Plaunlil':'lonely','Lazy rlerzil':'lazy','fnghtened Pfrartnd':'frightened','Clectricity':'electricity','aadj':None,
 'shelfjelf':'shelf','Teputation':'reputation','Tepresentative':'representative','afterschool':'after-school','Dlow':'blow',
 'nightowl':'night owl','zookeeper':'zookeeper','summercamp':'summer camp','prooiem':'problem','everypoay':'everybody',
 'mianignt':'midnight','aauit':'adult','Weekeno':'weekend','aiviaing line':'dividing line','aaylignt':'daylight',
 'moneypox':'moneybox','Dgerand':'grand','Spotlght':'spotlight','Hiberate':'liberate','Dleak':'bleak','windxu':None,
 'YINGYU':None,'Miay':'May','playarole in':'play a role in','otherthings':None,'that are notobvious':None,'usualrjuzual':'usual',
 'Woralist':None,'geulard against sth':'guard against sth','European fjooro piton':'European','effortefat':'effort',
 'Tgredzuot':'graduate','score an owngoal':'score an own goal','Buiol':'Buñol','Huangguoshu waterfall':'Huangguoshu Waterfall',
 'Timo':'Timo','limo':'Timo','Usain':'Usain','usa in':'Usain','think so':'I think so','can\'t wait':'I can\'t wait',
 'you want to do':None,'very intelligent or skillful':None,'use it':None,'or damage':None,'or a society':None,'is important':None,
 'and effort':None,'in socialism':None,'happened to prevent it':None,'to ignore or forget something':None,'nall as a total':'in all',
 'form or entertainment':None,'here i am':'Here I am','Likely larkli':'likely','upcycle':'upcycle','up cycle':'upcycle',
 'aewarop':'dewdrop','aeaicate':'dedicate','Tost':'lost','Tazy':'lazy','Tast':'last',
}
# 被当成释义残行删掉、其实是词头的（沪教高中「词头 + 英文释义」）
KEEP = {
 'cost an arm and a leg':'cost an arm and a leg',"can't be bothered to do sth":"can't be bothered to do sth",
 "have a frog in one's throat":"have a frog in one's throat",'selloff having a lot of money':'well off',
 'paper towel a thick sheet of paper':'paper towel','domestic chore a regular task':'domestic chore',
 'solar-power battery':'solar-power battery','stewed beef':'stewed beef','steamed bun':'steamed bun','coconut milk':'coconut milk',
 'hay wagon':'hay wagon','arts and crafts':'arts and crafts','have a row with':'have a row with','detective story':'detective story',
 'impose.. on':'impose... on','take... for granted':'take... for granted','stacks of':'stacks of','deprive... of':'deprive... of',
 'chill out':'chill out','bucket list':'bucket list','give something away':'give something away','marine ecosystem':'marine ecosystem',
 'tin cup':'tin cup','three strikes and you are out':'three strikes and you are out','g o to great lengths to do sth':'go to great lengths to do sth',
}
# 沪教高中（073-079）没有音标的行大多是上一词的英文释义续行，只留这些真词头
HJ_KEEP = {'time capsule','paper towel','aragon boat','dragon boat','rubbish dump','put... aside','pay regard to','domestic chore','rock band',
 'solar-power battery','stewed beef','steamed bun','gap year','life expectancy the','neon light','pots of money','coconut milk',
 'stealth marketing','nail Clippers','hay wagon','autobiographical novel','arts and crafts','have a row with','detective story',
 'Sketch pad','walrus-ivory carving','macaroni and cheese','impose... on','take... for granted','stacks of','deprive... of','chill out',
 'bucket list','give something away','marine ecosystem','tin cup','be owner by somebody','get a kick out of','video clip','belong to'}
HJ_FIX = {'aragon boat':'dragon boat','life expectancy the':'life expectancy','nail Clippers':'nail clippers','Sketch pad':'sketch pad',
 'be owner by somebody':'be owned by somebody'}
# 第二轮：词典里查得到但其实是识别错的（d 认成 a、l 认成 t 等）
FIX.update({
 'p. m. abor':'p.m.','ady':'fully','less Ales':'less','alot of':'a lot of','once ana for all':'once and for all','luck aniak':'luck',
 'aragon':'dragon','arent are not':"aren't = are not",'armin arm':'arm in arm','arum':'drum','ary':'dry','ata time':'at a time',
 'ought to atx':'ought to','aue to':'due to','link auge':'link','aull':'dull','beara':'beard','bena':'bend','bil':'bill',
 'bily goat':'billy goat','Bing owen owen':'Bing Dwen Dwen','bona':'bond','Beijing roast':'Beijing roast duck','cara':'card',
 'carn':'earn','cong':'whenever','cutout':'cut out','da':None,'Dase':'base','Dring... under control':'bring... under control',
 'eary':None,'fallin Love with':'fall in love with','abnormal feb normal':'abnormal','shade ferd':'shade','fi':'fill','fina':'find',
 'garand':'grand','geo all out':'go all out','GOLL':None,'gorin':'grin','on hana':'on hand','having... class':'have... class',
 'Bing Dwen Dwen':'Bing Dwen Dwen','mobile homen':'mobile home','hord':'hold','ki horta':'kilometre','town housen':'town house',
 'ina hurry':'in a hurry','date back Ito...':'date back to...','year jura':None,'acknowledge lak nord':'acknowledge',"I'm lam":"I'm",
 'leto of':'let go of','lett':'left','little by litle':'little by little','eve liv':'eve','admire lady mara':'admire','admire lode maro':'admire',
 'make the mostow':'make the most of','Mt':None,'nall':'hall','nara':'happen','netto':'next to','unique flu nik':'unique',
 'announce la noons':'announce','olack':'lack','Chinese operan':'Chinese opera','osage':'edge','lots ot':'lots of','activity paek toti':'activity',
 'take partin':'take part in','putin':'put on','reta':'yield','rubout of':'run out of','sare':'sore','seagrams':'seagrass','sec':'sec',
 'yourselves selz':'yourselves','except fit sept':'except','tate':None,'Tate':None,'Teed':'feed','tena':None,'Tittle by little':'little by little',
 'La tomatino':'La Tomatina','unity vu not':'unity','walt':'wait','be wiling to do something':'be willing to do something',
 'be wiling to do sth':'be willing to do sth','set wooton':'set off','analyse name ze':'analyse','leave... zenina':'leave... behind',
 'zookeeper':'zookeeper','o Chet jem':'chef','hana':'hand','mixup':'mix-up','p. ss':None,'timezone':'time zone','Papa westra':'Papa Westray',
 'the shaka':'the haka','dim sim':'dim sum','Hubert hutson':'Hubert Hudson','Langston hughes':'Langston Hughes','the kremlin':'the Kremlin',
})
# 看着像专名但是要学的词块（文化、食物、节日等），留下
KEEP_CAP = {'AI','Beijing roast duck','Mapo tofu','Gongbao chicken','Dongpo pork','Guoqiao Rice Noodles','Spring Festival couplet',
 'dragon-boat Festival','Dragon Boat Festival','coming-of-age Day','Taoist priest','Sichuan pepper','Sea of Clouds','Shot-put','Poet Laureate',
 'Heimlich manoeuvre','Common Era','Happy Birthday','Congratulations','Are you OK',"It's OK",'play Chinese chess','the Silver screen',
 'the Silk Road','the Yellow River','Orientation Day','Cheer Mire','Bing Dwen Dwen','Jade Rabbit','Achilles\' heel','Achilles\''}
CAP_FIX = {'Cheer Mire':'cheer','dragon-boat Festival':'Dragon Boat Festival','Shot-put':'shot put','the Silver screen':'the silver screen',
 'Achilles\'':"Achilles' heel",'o Skateboarding':'skateboarding'}
DROP_HEAD = {'Check Your Progress','Communication Workshop','Getting Ready','Reading Club','Speaking Workshop','Topic Talk','Writing Workshop',
 'Lesson B','P. IS','P. SI','ISBN','UNESCO four','and Museum','Tadpoles'}
CAP_FIX.update({'Keep... alive':'keep... alive','Leave... alone':'leave... alone','Slice... off':'slice... off','bring... to Life':'bring... to life',
 'in prison A':'in prison','shy Jar':'shy','to-do List':'to-do list'})
