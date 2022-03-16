import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile

moduleName = 'pf2e_tools'
typeString = {'type': 'string'}
typeFormattedText = {'type': 'formattedtext'}
staticModifier = {'static' : 'true'}
typeNumber = {'type': 'number'}
actionParser = {'1' : '[a]&#141;', '2' : '[a]&#143;', '3' : "[a]&#144;", 'R' : '[a]&#157;', 'F' : '[a]&#129;'}
numbersToProperNumber = {0 : 'Cantrips', 1 : '1st', 2 : '2nd', 3 : '3rd', 4 : '4th', 5 : '5th', 6 : '6th', 7 : '7th', 8 : '8th', 9 : '9th', 10 : '10th'}
numbersToWordNumber = {1 : 'Once', 2 : 'Twice', 3 : 'Three', 4 : 'Four', 5 : 'Five', 6 : 'Six', 7 : 'Seven', 8 : 'Eight', 9 : 'Nine'}
newline = '[newline]'

def stringFormatter(s):
    if s is None:
        return ''
    if s is int:
        return str(s)
    entryRaw = s
    entrySafe = ''
    for split in re.split('{|}', entryRaw):
        parsing = split
        if re.search('(@as+)\s', parsing) is not None:
            stringEnding = split[len(split) - 1]
            parsing = actionParser[str(stringEnding)]
        else:
            parsing = re.sub('@([a-zA-Z]+)\s', '', parsing)
            if parsing.find('||') != -1:
                parsing = re.split('\|\|', parsing)[1]
            parsing = re.sub('\|(.+)', '', parsing)
        entrySafe += parsing.replace('\n', ' ')
    return entrySafe


def activityToString(activity, isSymbol=True):
    if activity is None:
        return ''
    output = ''
    unitType = ''
    if 'unit' in activity:
        unitType = activity.get('unit')
    if 'number' in activity and unitType == 'action':
        if isSymbol:
            output = actionParser[str(activity.get('number'))]
        else:
            output += (str)(activity.get('number'))
    if not isSymbol:
        output += unitType
    if unitType == 'reaction' and isSymbol:
        output = actionParser['R']
    if unitType == 'free':
        if isSymbol:
            output = actionParser['F']
        else:
            output += 'action'
    return output

def entriesToXML(parentXML, entries, skipTypes=[]):
    if entries is None:
        return
    for entry in entries:
        if type(entry) is not dict:
            baseEntry = ET.SubElement(parentXML, 'p')
            baseEntry.text = stringFormatter(entry)
        else:
            entryType = entry.get('type')
            if entryType in skipTypes:
                continue
            entryTypeToXML(parentXML, entry, entryType)

def entryTypeToXML(parentXML, entry, entryType):
    if entryType == 'successDegree' or entryType == 'suceessDegree':
        successDegreeToXML(parentXML, entry.get('entries'))
    elif entryType == 'list':
        listToXML(parentXML, entry.get('items'))
    elif entryType == 'table':
        tableToXML(parentXML, entry.get('rows'), entry.get('footnotes') if 'footnotes' in entry else '')
    elif entryType == 'ability':
        abilityToXML(parentXML, entry)
    elif entryType == 'pf2-options':
        pf2_optionsToXML(parentXML, entry.get('items'))
    elif entryType == 'hr':
        hrToXML(parentXML, entry.get('entries'))
    elif entryType == 'affliction':
        afflictionToXML(parentXML, entry)
    elif entryType == 'lvlEffect':
        lvlEffectToXML(parentXML, entry.get('entries'))
    elif entryType == 'item':
        itemEntryTypeToXML(parentXML, entry.get('entries'))
    elif entryType == 'pf2-sample-box':
        pf2SampleBoxToXML(parentXML, entry)
    elif entryType == 'statblock':
        return
    elif entryType == 'attack':
        createStringTypeElement(parentXML, 'p', attackStringFromAttacks([entry], entry.get('range')))
    else:
        print('Unhandled Entry type: ' + entry.get('type'))

def pf2SampleBoxToXML(parentXML, dictionary):
    titleElement = ET.SubElement(parentXML, 'h')
    titleElement.text = dictionary.get('name')
    boxElement = ET.SubElement(parentXML, 'p')
    entriesToXML(boxElement, dictionary.get('entries'))

def itemEntryTypeToXML(parentXML, itemList):
    entriesToXML(parentXML, itemList)

def lvlEffectToXML(parentXML, entries):
    for entry in entries:
        entryElement = ET.SubElement(parentXML, 'p')
        entryElement.text = boldString(stringFormatter(entry.get('range'))) + ' '
        entryElement.text += stringFormatter(entry.get('entry'))

def afflictionToXML(parentXML, dictionary):
    titleElement = ET.SubElement(parentXML, 'p')
    titleElement.text = boldString(dictionary.get('name')) + ' '
    titleElement.text += '(' + listToString(dictionary.get('traits')) + '); '
    if 'level' in dictionary:
        titleElement.text += 'Level ' + str(dictionary.get('level')) + '; '
    if dictionary.get('note') is not None:
        titleElement.text += stringFormatter(dictionary.get('note'))
    for stage in dictionary.get('stages'):
        stageElement = ET.SubElement(parentXML, 'p')
        stageElement.text = boldString('Stage ' + str(stage.get('stage')) + ' ')
        stageElement.text += stringFormatter(stage.get('entry')) + ' '
        stageElement.text += '(' + stringFormatter(stage.get('duration')) + ').'

def tableToXML(parentXML, rows, footnotes=[]):
    table = ET.SubElement(parentXML, 'table')
    for row in rows:
        tableRow = ET.SubElement(table, 'tr')
        rowToXML(tableRow, row)
    if footnotes:
        for footnote in footnotes:
            footnoteBody = ET.SubElement(parentXML, 'p')
            footnoteBody.text = stringFormatter(footnote)


def rowToXML(parentXML, rowInfo):
    for column in rowInfo:
        columnXML = ET.SubElement(parentXML, 'td')
        columnXML.text = stringFormatter(column)


def pf2_optionsToXML(parentXML, items):
    for item in items:
        boldTextAndBody(parentXML, item.get('name'), item.get('entries')[0])


def hrToXML(parentXML, entries):
    for entry in entries:
        paragraph = ET.SubElement(parentXML, 'p')
        paragraph.text = stringFormatter(entry)


def successDegreeToXML(parentXML, success):
    root = ET.SubElement(parentXML, 'list')
    for states in success:
        successRate = ET.SubElement(root, 'li')
        successRate.text = boldString(states)
        successRate.text = stringFormatter(success.get(states))


def listToXML(parentXML, list):
    root = ET.SubElement(parentXML, 'list')
    for item in list:
        bulletPoint = ET.SubElement(root, 'li')
        if type(item) is str:
            bulletPoint.text = stringFormatter(item)
        elif type(item) is dict:
            entryTypeToXML(root, item, item.get('type'))
        else:
            print('unhandled list type: ' + str(type(item)))


def boldTextAndBody(parentXML, boldText, bodyText):
    root = ET.SubElement(parentXML, 'p')
    root.text = boldString(boldText)
    root.text += stringFormatter(bodyText)
    
def boldString(string):
    return '<b>' + stringFormatter(string) + '</b>'

def abilityToXML(parentXML, dictionary):
    titleField = ET.SubElement(parentXML, 'p')
    titleField.text = ''
    if 'name' in dictionary:
        titleField.text += boldString(dictionary.get('name')) + ' '
    else:
        titleField.text = boldString('Activate')
    if 'activity' in dictionary:
        activity = activityToString(dictionary.get('activity'))
        titleField.text += boldString(activity) + ' '
    if 'components' in dictionary:
        for component in dictionary.get('components'):
            titleField.text += stringFormatter(component) + ' '
    if 'traits' in dictionary:
        titleField.text += '['
        titleField.text += listToString(dictionary.get('traits')).upper()
        titleField.text += ']'
    if 'prerequisites' in dictionary:
        boldTextAndBody(parentXML, 'Prerequisites', dictionary.get('prerequisites'))
    if 'requirements' in dictionary:
        boldTextAndBody(parentXML, 'Requirements', dictionary.get('requirements'))
    if 'trigger' in dictionary:
        boldTextAndBody(parentXML, 'Trigger', dictionary.get('trigger'))
    if 'frequency' in dictionary:
        boldTextAndBody(parentXML, 'Frequency', frequencyToString(dictionary.get('frequency')))
    if 'entries' in dictionary:
        entriesToXML(parentXML, dictionary.get('entries'))

def frequencyToString(frequency):
    if type(frequency) is str:
        return frequency
    output = ''
    if type(frequency) is dict:
        if frequency.get('freq'):
            timeWord = ' per '
            if frequency.get('freq') > 2:
                timeWord = ' times '
            if frequency.get('recurs'):
                timeWord = ' every '
            if frequency.get('interval'):
                timeWord += str(frequency.get('interval')) + ' '
            output += numbersToWordNumber[frequency.get('freq')]
        if frequency.get('unit'):
            output += timeWord + frequency.get('unit')
        if frequency.get('special'):
            if len(output) > 0:
                output += '; '
            output += frequency.get('special')
    return output

def xmlToFormattedString(xmlParent):
    output = ''
    ET.indent(xmlParent, level=0, space='')
    arrayHolder = ET.tostringlist(xmlParent, 'unicode', 'text')
    newLine = ''
    for ability in arrayHolder:
        if ability == '\n':
            continue
        output += newLine + ability
        newLine = newline
    output = output.replace('<b>', newline)
    output = output.replace('</b>', '')
    return output

def entriesToString(entries):
    output = ''
    if type(entries) is None:
        return output
    holding = ET.Element('body')
    entriesToXML(holding, entries)
    output = xmlToFormattedString(holding)
    return output

def abilityToNameAndDescription(parentXML, dictionary, oneLine = False, oneLineName = ''):
    nameString = ''
    descriptionString = ''
    if 'activity' in dictionary:
        nameString += activityToString(dictionary.get('activity')) + ' '
    if 'name' in dictionary:
        nameString += dictionary.get('name') + ' '
    else:
        nameString = ''
    if 'traits' in dictionary:
        nameString += '('
        nameString += listToString(dictionary.get('traits')).upper()
        nameString += ')'
    newLineCharacter = ''
    if 'prerequisites' in dictionary:
        descriptionString += '- Prerequisites: ' + dictionary.get('prerequisites')
        newLineCharacter = newline
    if 'requirements' in dictionary:
        descriptionString += newLineCharacter + '- Requirements: ' + dictionary.get('requirements')
        newLineCharacter = newline
    if 'trigger' in dictionary:
        descriptionString += newLineCharacter + '- Trigger: ' + dictionary.get('trigger')
        newLineCharacter = newline
    if 'frequency' in dictionary:
        descriptionString += newLineCharacter + '- Frequency: ' + frequencyToString(dictionary.get('frequency'))
        newLineCharacter = newline
    if 'entries' in dictionary:
        descriptionString += newLineCharacter + entriesToString(dictionary.get('entries'))
    if oneLine:
        createStringTypeElement(parentXML, oneLineName, nameString + newline + descriptionString)
    else:
        createStringTypeElement(parentXML, 'name', nameString)
        createStringTypeElement(parentXML, 'desc', descriptionString)

def abilityToString(dictionary):
    output = ''
    holding = ET.Element('p')
    abilityToNameAndDescription(holding, dictionary, True, 'line')
    output = xmlToFormattedString(holding)
    return output

def monsterAbilityToXML(parentXML, dictionary, number):
    bodyElement = ET.SubElement(parentXML, f'id-{number:05}')
    abilityToNameAndDescription(bodyElement, dictionary)

def optionListToString(optionsList):
    output = ''
    endLength = len(optionsList)
    for i in range(0, endLength):
        output += stringFormatter(optionsList[i])
        if i < endLength - 1:
            output += ', or '
    return output

def listToString(list, inbetween = ', '):
    output = ''
    if list is None:
        return ''
    endLength = len(list)
    for i in range(0, endLength):
        output += stringFormatter(list[i])
        if i < endLength - 1:
            output += inbetween
    return output

def createNumberTypeElement(parentXML, elementName, elementBody):
    genericBody = ET.SubElement(parentXML, elementName, typeNumber)
    genericBody.text = ''
    if elementBody is not None:
        genericBody.text = str(elementBody)

def createStringTypeElement(parentXML, elementName, elementBody):
    genericBody = ET.SubElement(parentXML, elementName, typeString)
    genericBody.text = ''
    if elementBody is not None:
        genericBody.text = stringFormatter(elementBody)

def createListToXMLString(parentXML, list, elementName, toUpper=True):
    listElement = ET.SubElement(parentXML, elementName, typeString)
    output = ''
    if list:
        endLength = len(list)
        for i in range(0, endLength):
            word = stringFormatter(list[i])
            word = word.upper() if toUpper else word
            output += word
            if i < endLength - 1:
                output += ', '
    listElement.text = output


def spellHeightenedListToXML(parentXML, list, elementName='heightened'):
    heightenedElement = ET.SubElement(parentXML, elementName, typeFormattedText)
    for entry in list:
        entryBodyElement = ET.SubElement(heightenedElement, 'p')
        entryBodyElement.text = '(+ ' + str(entry.get('level')) + ') '
        if type(entry.get('entry')) is str:
            entryBodyElement.text += stringFormatter(entry.get('entry'))
        else:
            entriesToXML(heightenedElement, entry.get('entry'))
        
    

def writeFeatDBFile(root):
    file = open('feats-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    featElement = ET.SubElement(root, 'feat')
    category = ET.SubElement(featElement, 'category', {'name': moduleName})

    for feat in data:
        featBody = ET.SubElement(category, f'id-{id:05}')
        access = ET.SubElement(featBody, 'access', typeString)
        access.text = 'PF2e Tools'

        action = ET.SubElement(featBody, 'action', typeString)
        action.text = ''
        if 'activity' in feat:
            action.text = activityToString(feat.get('activity'), False)

        archetype = ET.SubElement(featBody, 'archetype', typeString)
        archetype.text = ''
        if 'featType' in feat:
            if feat.get('featType') is not None:
                featType = feat.get('featType')
                if 'archetype' in featType:
                    featArchetypeRestriction = featType.get('archetype')
                    if type(featArchetypeRestriction) != bool:
                        for i in range(0, len(featArchetypeRestriction)):
                            archetype.text += featArchetypeRestriction[i]
                            if(i < len(featArchetypeRestriction) - 1):
                                archetype.text += ', '

        effectsBenefits = ET.SubElement(
            featBody, 'effectsbenefits', typeFormattedText)
        if 'entries' in feat:
            entriesToXML(effectsBenefits, feat.get('entries'))

        createStringTypeElement(featBody, 'frequency', frequencyToString(feat.get('frequency')))

        level = ET.SubElement(featBody, 'level', typeNumber)
        level.text = (str)(1)
        if 'level' in feat:
            level.text = (str)(feat.get('level'))

        # This is constant and also I have no idea if it is used
        levelApplied = ET.SubElement(featBody, 'level_applied', typeNumber)
        levelApplied.text = '0'

        featName = ET.SubElement(featBody, 'name', typeString)
        featName.text = 'No Name'

        if 'name' in feat:
            featName.text = feat.get('name')

        prerequisites = ET.SubElement(featBody, 'prerequisites', typeString)
        prerequisites.text = ''

        if 'prerequisites' in feat:
            prerequisites.text = stringFormatter(feat.get('prerequisites'))

        requirements = ET.SubElement(featBody, 'requirements', typeString)
        requirements.text = ''

        if 'requirements' in feat:
            requirements.text = stringFormatter(feat.get('requirements'))

        # This needs to be manually added so don't use it
        shortBenefits = ET.SubElement(featBody, 'shortbenefits', typeString)
        shortBenefits.text = ''

        source = ET.SubElement(featBody, 'source', typeString)
        source.text = ''
        if 'source' in feat:
            source.text = stringFormatter(feat.get('source'))

        special = ET.SubElement(featBody, 'special', typeFormattedText)
        specialText = ET.SubElement(special, 'p')
        specialText.text = ''
        if 'special' in feat:
            specialText.text = stringFormatter(feat.get('special'))

        traits = ET.SubElement(featBody, 'traits', typeString)
        traits.text = ''
        if 'traits' in feat:
            for i in feat.get('traits'):
                traits.text += i.upper() + ' '

        trigger = ET.SubElement(featBody, 'trigger', typeString)
        trigger.text = ''
        if 'trigger' in feat:
            trigger.text = stringFormatter(feat.get('trigger'))
        id = id + 1



def writeBackgrounds(rootXML):
    file = open('backgrounds-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    featElement = ET.SubElement(rootXML, 'background')
    category = ET.SubElement(featElement, 'category', {'name': moduleName})
    for background in data:
        backgroundBody = ET.SubElement(category, f'id-{id:05}')

        boostsBody = ET.SubElement(backgroundBody, 'abilityboost', typeString)
        if 'boosts' in background:
            boostsBody.text = ''
            endLength = len(background.get('boosts'))
            for i in range(0, endLength):
                boostsBody.text += stringFormatter(background.get('boosts')[i])
                if i < endLength - 1:
                    if background.get('boosts')[i + 1] != 'Free':
                        boostsBody.text += ', or '
                    else:
                        break

        loreBody = ET.SubElement(backgroundBody, 'loreskill', typeString)
        if 'lore' in background: 
            loreBody.text = optionListToString(background.get('lore'))

        nameBody = ET.SubElement(backgroundBody, 'name', typeString)
        if 'name' in background:
            nameBody.text = stringFormatter(background.get('name')).upper()

        featBody = ET.SubElement(backgroundBody, 'skillfeat', typeString)
        if 'feat' in background:
            if type(background.get('feat')) is list:
                featBody.text = optionListToString(background.get('feat'))
            else:
                featBody.text = stringFormatter(background.get('feat'))

        sourceBody = ET.SubElement(backgroundBody, 'source', typeString)
        if 'source' in background:
            sourceBody.text = stringFormatter(background.get('source'))

        entriesGroup = ET.SubElement(backgroundBody, 'text', typeFormattedText)
        if 'entries' in background:
            entriesToXML(entriesGroup, background.get('entries'))

        skillsBody = ET.SubElement(backgroundBody, 'trainedskill', typeString)
        if 'skills' in background:\
            skillsBody.text = optionListToString(background.get('skills'))
        
        id += 1

def writeSingleSpell(parentXML, spell, id, spellNameAppend = ''):
    spellBody = ET.SubElement(parentXML, f'id-{id:05}')
    createStringTypeElement(spellBody, 'name', spell.get('name') + spellNameAppend)
    createStringTypeElement(spellBody, 'source', spell.get('source'))
    spellTypeString = 'SPELL'
    if spell.get('focus'):
        spellTypeString = 'FOCUS'
    createStringTypeElement(spellBody, 'spelltype', spellTypeString)
    createStringTypeElement(spellBody, 'spelltypelabel', spellTypeString[0])
    createListToXMLString(spellBody, spell.get('traits'), 'traits')
    areaElement = ET.SubElement(spellBody, 'area', typeString)
    if 'area' in spell:
        areaElement.text = stringFormatter(spell.get('area').get('entry'))
    createStringTypeElement(spellBody, 'cost', spell.get('cost'))
    createStringTypeElement(spellBody, 'duration', spell.get('duration').get('entry'))
    effectsElement = ET.SubElement(spellBody, 'effects', typeFormattedText)
    entriesToXML(effectsElement, spell.get('entries'), ['successDegree'])
    if spell.get('heightened').get('heightened'):
        if spell.get('heightened').get('plus_x') is not None:
            properNumber = '(+' + str(spell.get('heightened').get('plus_x').get('level')) + ')'
            heightenedEntry = stringFormatter(spell.get('heightened').get('plus_x').get('entry'))
            heightenedElement = ET.SubElement(spellBody, 'heightened', typeFormattedText)
            boldTextAndBody(heightenedElement, properNumber, heightenedEntry)
        if spell.get('heightened').get('x') is not None:
            spellHeightenedListToXML(spellBody,  spell.get('heightened').get('x'))
    createNumberTypeElement(spellBody, 'level', spell.get('level'))
    createStringTypeElement(spellBody, 'requirements', spell.get('requirements'))
    createStringTypeElement(spellBody, 'savingthrow', spell.get('savingThrow'))
    createListToXMLString(spellBody, spell.get('traditions'), 'traditions', False)
    rangeElement = ET.SubElement(spellBody, 'range', typeString)
    if 'range' in spell:
        rangeElement.text = stringFormatter(spell.get('range').get('entry'))
    createStringTypeElement(spellBody, 'trigger', spell.get('trigger'))
    components = []
    if spell.get('components').get('M'):
        components.append('material')
    if spell.get('components').get('S'):
        components.append('somatic')
    if spell.get('components').get('V'):
        components.append('verbal')
    castingElement = ET.SubElement(spellBody, 'casting', typeString)
    if 'entry' in spell.get('cast'):
        castingElement.text = stringFormatter(spell.get('cast').get('entry'))
    else:
        castingElement.text = activityToString(spell.get('cast'))
    castingElement.text += ' ' + listToString(components)
    createStringTypeElement(spellBody, 'targets', spell.get('targets'))
    spellListElement = ET.SubElement(spellBody, 'spelllists', typeString)
    superScriptsList = []
    if spell.get('heightened').get('heightened'):
        superScriptsList.append('H')
    if 'Uncommon' in spell.get('traits'):
        superScriptsList.append('U')
    if 'Rare' in spell.get('traits'):
        superScriptsList.append('R')
    createStringTypeElement(spellBody, 'superscripts', listToString(superScriptsList))
    entryDictionaryHolder = {}
    for entry in spell.get('entries'):
        if type(entry) is dict:
            if entry.get('type') == 'successDegree':
                entryDictionaryHolder = entry.get('entries')
    createStringTypeElement(spellBody, 'critfailure', entryDictionaryHolder.get('Critical Failure'))
    createStringTypeElement(spellBody, 'failure', entryDictionaryHolder.get('Failure'))
    createStringTypeElement(spellBody, 'success', entryDictionaryHolder.get('Success'))
    createStringTypeElement(spellBody, 'critsuccess', entryDictionaryHolder.get('Critical Success'))
    actionsElement = ET.SubElement(spellBody, 'actions')
    return spellBody

def writeSpells(rootXML):
    file = open('spells-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    spellElement = ET.SubElement(rootXML, 'spell')
    category = ET.SubElement(spellElement, 'category', {'name': moduleName})
    for spell in data:
        writeSingleSpell(category, spell, id)
        id += 1

def perceptionStringFromMonster(beast):
    if beast.get('perception') is None:
        return ''
    output = 'Perception +' + str(beast.get('perception').get('default')) + '; '
    for perception in beast.get('perception'):
        if perception == 'default':
            continue
        output += '(+' + str(beast.get('perception').get(perception)) + ' ' + perception + '); '
    if beast.get('senses') is not None:
        for sense in beast.get('senses'):
            if sense == 'other':
                output += listToString(beast.get('senses').get(sense)) + ', '
            else:
                for typing in beast.get('senses').get(sense):
                    output += '(' + sense + ') ' + typing + ', '
        output = output[:-2]

    return output

def skillStringFromMonster(skillsDictionary = {}):
    output = ''
    for skill in skillsDictionary:
        output += skill + ' +' + str(skillsDictionary.get(skill).get('default'))
        for specificSkill in skillsDictionary.get(skill):
            if specificSkill == 'default':
                continue
            output += '(+' + str(skillsDictionary.get(skill).get(specificSkill)) + ' ' + specificSkill + ')'
        output += ', '
    return output[:-2]

def speedStringFromSpeedDictionary(speedDict = {}):
    output = ''
    if speedDict is None:
        return output
    for speeds in speedDict:
        if speeds == 'abilities':
            continue
        if speeds == 'walk':
            output += str(speedDict.get(speeds))
        else:
            output += speeds + ' ' + str(speedDict.get(speeds))
        output += ' feet, '
    output = output[:-2]
    if speedDict.get('abilities') is not None:
        speedAbilities = listToString(speedDict.get('abilities'))
        output += '; ' + speedAbilities
    return output

def weaknessAndResistanceToString(list):
    resistanceString = ''
    if list is not None:
        resistanceLock = False
        for resistance in list:
            if resistanceLock:
                resistanceString += ', '
            resistanceString += resistance.get('name')
            if resistance.get('amount') is not None:
                resistanceString += ' ' + str(resistance.get('amount'))
            if resistance.get('note') is not None:
                resistanceString += ' ' + str(resistance.get('note')) 
            resistanceLock = True
    return resistanceString

def attackStringFromAttacks(attackList = [], attackType = 'Melee'):
    attackString = ''
    multipleMeleeLock = False
    if attackList is None:
        return ''
    for attack in attackList:
        if type(attack) is None:
            continue
        if attack.get('range') != attackType:
            continue
        if multipleMeleeLock:
            attackString += newline
        attackString += actionParser['1'] + ' '
        attackString += stringFormatter(attack.get('name'))
        attackString += ' +' + str(attack.get('attack'))
        attackString += ' (' + listToString(attack.get('traits')) + '), Damage '
        attackString += stringFormatter(attack.get('damage')) + ' '
        if attack.get('effects'):
            if len(attack.get('effects')) > 0:
                attackString += 'plus ' + listToString(attack.get('effects'))
        multipleMeleeLock = True
        if attack.get('noMAP'):
            attackString += ', no multiple attack penalty'
    return attackString

def spellEntriesToString(entries):
    output = ''
    spellLock = False
    if entries is None:
        return ''
    for spell in entries:
        if spellLock:
            output += newline
        if spell == 'constant':
            output += 'Constant: ' + spellEntriesToString(entries.get(spell))
        else:
            output += spellNumberToString(entries.get(spell), spell)
        spellLock = True
    return stringFormatter(output)


def spellNumberToString(numberDictionary, level):
    output = ''
    if level == '0':
        output += 'Cantrip ('
    if numberDictionary.get('level') is not None:
        output += numbersToProperNumber[int(numberDictionary.get('level'))]
        if level == '0':
            output += ')'
    else:
        output += numbersToProperNumber[int(level)]
    output += ': '
    if numberDictionary.get('slots'):
        output += f"({numberDictionary.get('slots')} slots) "
    output += spellListToString(numberDictionary.get('spells'))
    return output

def spellListToString(listing):
    output = ''
    spellLock = False
    for spell in listing:
        if spellLock:
            output += ', '
        output += spell.get('name')
        if spell.get('amount') is not None:
            output += ' (' + str(spell.get('amount')) + ')'
        if spell.get('notes') is not None:
            output += ' (' + listToString(spell.get('notes')) + ')'
        spellLock = True
    return output

def spellFromSpellCasting(casting):
    genericSpellString = ''
    if casting is None:
        return genericSpellString
    genericSpellString += casting.get('name')
    if casting.get('DC') is not None:
        genericSpellString += ' DC ' + str(casting.get('DC'))
    if casting.get('attack') is not None:
        genericSpellString += ' attack +' + str(casting.get('attack'))
    genericSpellString += '; '
    if casting.get('fp') is not None:
        genericSpellString += '(' + str(casting.get('fp')) + ' Focus Point) '
    genericSpellString += spellEntriesToString(casting.get('entry'))
    return genericSpellString

def acDictToString(acDict):
    acText = ''
    if acDict is not None:
        acText += str(acDict.get('default'))
        for acEntries in acDict:
            if acEntries == 'default' or acEntries == 'abilities':
                continue
            acText += ' (' + str(acDict.get(acEntries)) + ' ' + acEntries + ' ' + ')'
        acAbilities = acDict.get('abilities')
        if acAbilities is not None:
            acText += '; ' + acAbilities + ';'
    return acText

def immunitiesToString(immunityDict):
    immunitiesString = ''
    if immunityDict is not None:
        immunities = []
        if immunityDict.get('damage') is not None:
            immunities.extend(immunityDict.get('damage'))
        if immunityDict.get('condition') is not None:
            immunities.extend(immunityDict.get('condition'))
        immunitiesString = listToString(immunities)
    return immunitiesString

def parseMonsterSpells(monsterSpellListXML, spellLists, characterLevel):
    spellListData = {}
    file = open('spells-sublist-data.json')
    data = json.load(file)
    file.close()
    for spell in data:
        spellListData[spell.get('name').lower()] = spell
    spellListID = 1
    for spellList in spellLists:
        spellEntries = spellList.get('entry')
        spellIdElement = ET.SubElement(monsterSpellListXML, f'id-{spellListID:05}')
        createNumberTypeElement(spellIdElement, 'cl', characterLevel)
        createNumberTypeElement(spellIdElement, 'slotstatmod', 0)
        spellAttackBonusNumber = 0
        DCTotalNumber = 10
        if spellList.get('fp'):
            createStringTypeElement(spellIdElement, 'castertype', 'points')
            createNumberTypeElement(spellIdElement, 'powerclass', 1)
        if spellList.get('type') == 'Spontaneous':
            createStringTypeElement(spellIdElement, 'castertype', 'spontaneous')
        createStringTypeElement(spellIdElement, 'label', spellList.get('name'))
        traditionString = ''
        if spellList.get('tradition'):
            traditionString = spellList.get('tradition').lower()
        createStringTypeElement(spellIdElement, 'tradition', traditionString)
        if spellList.get('DC'):
            DCTotalNumber = spellList.get('DC')  
        if spellList.get('attack'):
            spellAttackBonusNumber = spellList.get('attack')
        createNumberTypeElement(spellIdElement, 'spellatkbonus', spellAttackBonusNumber)
        DCElementBody = ET.SubElement(spellIdElement, 'dc')
        createNumberTypeElement(DCElementBody, 'abilitymod', 0)
        createNumberTypeElement(DCElementBody, 'item', 0)
        createNumberTypeElement(DCElementBody, 'misc', DCTotalNumber - 10)
        createNumberTypeElement(DCElementBody, 'prof', 0)
        createNumberTypeElement(DCElementBody, 'roll', 0)
        createNumberTypeElement(DCElementBody, 'rolltempmod', 0)
        createNumberTypeElement(DCElementBody, 'tempmod', 0)
        createNumberTypeElement(DCElementBody, 'total', DCTotalNumber)
        levelsElementBody = ET.SubElement(spellIdElement, 'levels')
        for level in range(0, 11):
            countAllSpells = False
            levelElementBody = ET.SubElement(levelsElementBody, f'level{level}')
            createNumberTypeElement(levelElementBody, 'level', level)
            createNumberTypeElement(levelElementBody, 'maxprepared', 0)
            createNumberTypeElement(levelElementBody, 'totalcast', 0)
            createNumberTypeElement(levelElementBody, 'totalprepared', 0)
            spellListEntriesBody = ET.SubElement(levelElementBody, 'spells')
            availableSpells = 0
            spellEntry = spellEntries.get(str(level))
            if spellEntry:
                if level == 0 and spellEntry.get('level'):
                    availableSpells = spellEntry.get('level')
                elif spellEntry.get('slots'):
                    availableSpells = spellEntry.get('slots')
                elif spellList.get('type') != 'Prepared':
                    countAllSpells = True
                    availableSpells = 1
                spellFromDataList = spellEntry.get('spells')
                for i in  range(0, len(spellFromDataList)):
                    notes = ''
                    if spellListData.get(spellFromDataList[i].get('name').lower()) is None:
                        continue
                    spellBase = spellListData.get(spellFromDataList[i].get('name').lower())
                    if spellFromDataList[i].get('notes'):
                        notes = ' ' + listToString(spellFromDataList[i].get('notes'))
                    if spellFromDataList[i].get('amount'):
                        notes += ' (' + str(spellFromDataList[i].get('amount')) + ' time(s))'
                    spellBody = writeSingleSpell(spellListEntriesBody, spellBase, i + 1, notes)
                    preparedAmount = 1
                    if type(spellFromDataList[i].get('amount')) is int:
                        preparedAmount = spellFromDataList[i].get('amount')
                    if spellList.get('type') != 'Focus':
                        createNumberTypeElement(spellBody, 'prepared', preparedAmount)
                    if countAllSpells:
                        availableSpells += preparedAmount
                    createNumberTypeElement(spellBody, 'cast', 0)
                    createNumberTypeElement(spellBody, 'spcost', 1)
            createNumberTypeElement(spellIdElement, f'availablelevel{level}', availableSpells)
        spellListID += 1  

def writeMonsters(beastElement, createMonsterSpellList = False):
    file = open('bestiary-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    category = ET.SubElement(beastElement, 'category', {'name': moduleName})
    for beast in data:
        beastBody = ET.SubElement(category, f'id-{id:05}')
        createStringTypeElement(beastBody, 'ac', acDictToString(beast.get('ac')))
        createStringTypeElement(beastBody, 'category', moduleName + ' ' + beast.get('source'))
        abilityModsEntry = beast.get('abilityMods')
        if abilityModsEntry is not None:
            createNumberTypeElement(beastBody, 'strength', abilityModsEntry.get('Str'))
            createNumberTypeElement(beastBody, 'dexterity', abilityModsEntry.get('Dex'))
            createNumberTypeElement(beastBody, 'constitution', abilityModsEntry.get('Con'))
            createNumberTypeElement(beastBody, 'intelligence', abilityModsEntry.get('Int'))
            createNumberTypeElement(beastBody, 'wisdom', abilityModsEntry.get('Wis'))
            createNumberTypeElement(beastBody, 'charisma', abilityModsEntry.get('Cha'))
        saves = beast.get('savingThrows')
        if saves is not None:
            createNumberTypeElement(beastBody, 'fortitudesave', saves.get('Fort').get('default'))
            createNumberTypeElement(beastBody, 'reflexsave', saves.get('Ref').get('default'))
            createNumberTypeElement(beastBody, 'willsave', saves.get('Will').get('default'))
            createStringTypeElement(beastBody, 'saveabilities', saves.get('abilities'))
        if beast.get('hardness') is not None:
            createStringTypeElement(beastBody, 'hardness', str(beast.get('hardness')))
        createNumberTypeElement(beastBody, 'hp', beast.get('hp')[0].get('hp'))
        hpAbilities = ''
        if beast.get('hp') is not None:
            for hpEntries in beast.get('hp'):
                if hpEntries.get('note') is not None:
                    hpAbilities += boldString(hpEntries.get('note')) + ' '
                hpAbilities += str(hpEntries.get('hp')) + ' '
                if hpEntries.get('abilities') is not None:
                    hpAbilities += listToString(hpEntries.get('abilities')) + ' '
            if hpAbilities.replace(' ', '').isdigit():
                hpAbilities = ''
        createStringTypeElement(beastBody, 'hpabilities', hpAbilities)        
        createStringTypeElement(beastBody, 'immunities', immunitiesToString(beast.get('immunities')))
        if beast.get('perception') is not None:
            createNumberTypeElement(beastBody, 'init', beast.get('perception').get('default'))
        else:
            createNumberTypeElement(beastBody, 'init', 0)
        languageString = ''
        if beast.get('languages') is not None:
            combinedLanguages = beast.get('languages').get('languages')
            combinedLanguages.extend(beast.get('languages').get('languageAbilities'))
            languageString = listToString(combinedLanguages)
        createStringTypeElement(beastBody, 'languages', languageString)
        createNumberTypeElement(beastBody, 'level', beast.get('level'))
        createStringTypeElement(beastBody, 'name', beast.get('name'))
        createStringTypeElement(beastBody, 'nonid_name', '')
        createStringTypeElement(beastBody, 'resistances', weaknessAndResistanceToString(beast.get('resistances')))
        createStringTypeElement(beastBody, 'weaknesses', weaknessAndResistanceToString(beast.get('weaknesses')))
        createStringTypeElement(beastBody, 'senses', perceptionStringFromMonster(beast))
        createStringTypeElement(beastBody, 'items', listToString(beast.get('items')))
        createStringTypeElement(beastBody, 'skills', skillStringFromMonster(beast.get('skills')))
        createStringTypeElement(beastBody, 'speed', speedStringFromSpeedDictionary(beast.get('speed')))
        createStringTypeElement(beastBody, 'spelldisplaymode', 'action')
        createStringTypeElement(beastBody, 'spellmode', 'standard')
        createStringTypeElement(beastBody, 'subcategory', '')
        textElement = ET.SubElement(beastBody, 'text', typeFormattedText)
        ET.SubElement(textElement, 'p')
        ET.SubElement(beastBody, 'token', {'type' : 'token'})
        traits = []
        if beast.get('rarity') is not None:
            traits.append(beast.get('rarity'))
        if beast.get('alignment') is not None:
            traits.append(beast.get('alignment'))
        if beast.get('size') is not None:
            traits.append(beast.get('size'))
        if beast.get('creatureType') is not None:
            traits.extend(beast.get('creatureType'))
        if beast.get('traits') is not None:
            traits.extend(beast.get('traits'))
        createStringTypeElement(beastBody, 'traits', listToString(traits))
        miscellaneousElement = ET.SubElement(beastBody, 'miscellaneous', typeFormattedText)
        miscellaneousText = ET.SubElement(miscellaneousElement, 'p')
        createStringTypeElement(beastBody, 'meleeatk', attackStringFromAttacks(beast.get('attacks')))
        createStringTypeElement(beastBody, 'rangedatk', attackStringFromAttacks(beast.get('attacks'), 'Ranged'))
        interactionAbilitiesElement = ET.SubElement(beastBody, 'actions_interactionabilities')
        if beast.get('abilitiesTop') is not None:
            for i in range(0, len(beast.get('abilitiesTop'))):
                monsterAbilityToXML(interactionAbilitiesElement, beast.get('abilitiesTop')[i], i + 1)
        offensiveProactiveElement = ET.SubElement(beastBody, 'actions_offensiveproactive')
        if beast.get('abilitiesBot') is not None:
            for i in range(0, len(beast.get('abilitiesBot'))):
                monsterAbilityToXML(offensiveProactiveElement, beast.get('abilitiesBot')[i], i + 1)
        reactiveAbilitiesElement = ET.SubElement(beastBody, 'actions_reactiveabilities')
        if beast.get('abilitiesMid') is not None:
            for i in range(0, len(beast.get('abilitiesMid'))):
                monsterAbilityToXML(reactiveAbilitiesElement, beast.get('abilitiesMid')[i], i + 1)
        innateSpellString = ''
        focusSpellString = ''
        focusPointBase = 0
        genericSpellString = ''
        if beast.get('spellcasting') is not None:
            for spellCasting in beast.get('spellcasting'):
                if spellCasting.get('type') == 'Innate':
                    innateSpellString += spellFromSpellCasting(spellCasting)
                elif spellCasting.get('type') == 'Focus':
                    focusSpellString += spellFromSpellCasting(spellCasting)
                    if spellCasting.get('fp'):
                        focusPointBase = spellCasting.get('fp')
                else:
                    genericSpellString += spellFromSpellCasting(spellCasting)
        createStringTypeElement(beastBody, 'classpowers', focusSpellString)
        createStringTypeElement(beastBody, 'innatespells', innateSpellString)
        createStringTypeElement(beastBody, 'spells', genericSpellString)
        ritualString = ''
        ritualLock = False
        if beast.get('rituals') is not None:
            for ritual in beast.get('rituals'):
                if ritualLock:
                    ritualString += newline
                if ritual.get('tradition') is not None:
                    ritualString += ritual.get('tradition') + ' Rituals '
                if ritual.get('DC') is not None:
                    ritualString += 'DC ' + str(ritual.get('DC'))
                ritualString += spellListToString(ritual.get('rituals'))
        focusPointElementBase = ET.SubElement(beastBody, 'sp')
        createNumberTypeElement(focusPointElementBase, 'base', focusPointBase)
        createNumberTypeElement(focusPointElementBase, 'item', 0)
        createNumberTypeElement(focusPointElementBase, 'misc', 0)
        createNumberTypeElement(focusPointElementBase, 'pointsused', 0)
        createNumberTypeElement(focusPointElementBase, 'tempmod', 0)
        createNumberTypeElement(focusPointElementBase, 'total', focusPointBase)
        spellsetElement = ET.SubElement(beastBody, 'spellset')
        if beast.get('spellcasting') and createMonsterSpellList:
            parseMonsterSpells(spellsetElement, beast.get('spellcasting'), beast.get('level'))
        id += 1

def writeAfflictions(rootXML):
    file = open('afflictions-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    afflictionElementHead = ET.SubElement(rootXML, 'affliction')
    category = ET.SubElement(afflictionElementHead, 'category', {'name': moduleName})
    for afflictionData in data:
        afflicitonBody = ET.SubElement(category, f'id-{id:05}')
        createStringTypeElement(afflicitonBody, 'name', afflictionData.get('name'))
        afflictionLevel = str(afflictionData.get('level') if afflictionData.get('level') else '')
        createStringTypeElement(afflicitonBody, 'traits', listToString(afflictionData.get('traits')))
        afflictionEntries = afflictionData.get('entries')
        afflictionElementsFromData = {}
        if afflictionEntries:
            if type(afflictionEntries[0]) == str:
                createStringTypeElement(afflicitonBody, 'text', stringFormatter(afflictionEntries[0]))
                afflictionElementsFromData = afflictionEntries[1]
            else:
                afflictionElementsFromData = afflictionEntries[0]
        
        createStringTypeElement(afflicitonBody, 'onset', afflictionElementsFromData.get('onset'))
        if afflictionElementsFromData.get('level'):
            afflictionLevel = stringFormatter(afflictionElementsFromData.get('level'))
        createStringTypeElement(afflicitonBody, 'level', afflictionLevel)
        savingThrowString = ''
        if afflictionElementsFromData.get('DC'):
            savingThrowString = str(afflictionElementsFromData.get('DC')) + 'DC '
        savingThrowString += stringFormatter(afflictionElementsFromData.get('savingThrow'))
        createStringTypeElement(afflicitonBody, 'saving_throw', savingThrowString)
        if afflictionElementsFromData.get('stages'):
            for stage in afflictionElementsFromData.get('stages'):
                stageNumber = stage.get('stage')
                stageString = stage.get('entry')
                if stage.get('duration'):
                    stageString += ' (' + stage.get('duration') + ')'
                createStringTypeElement(afflicitonBody, f'stage{stageNumber}', stageString)
        id += 1

def writeHazard(npcXML, hazardBody):
    file = open('hazards-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    category = ET.SubElement(npcXML, 'category', {'name': moduleName})
    for hazardData in data:
        hazardBody = ET.SubElement(category, f'id-{id:05}')
        ET.SubElement(hazardBody, 'actions_interactionabilities')
        ET.SubElement(hazardBody, 'actions_offensiveproactive')
        ET.SubElement(hazardBody, 'actions_reactiveabilities')
        createNumberTypeElement(hazardBody, 'charisma', 0)
        createNumberTypeElement(hazardBody, 'constitution', 0)
        createNumberTypeElement(hazardBody, 'dexterity', 0)
        createNumberTypeElement(hazardBody, 'intelligence', 0)
        createNumberTypeElement(hazardBody, 'strength', 0)
        createNumberTypeElement(hazardBody, 'wisdom', 0)
        createStringTypeElement(hazardBody, 'nonid_name', '')
        createStringTypeElement(hazardBody, 'npctype', 'Hazard')
        textElementUnused = ET.SubElement(hazardBody, 'text', typeFormattedText)
        ET.SubElement(textElementUnused, 'p')
        miscElementUnused = ET.SubElement(hazardBody, 'miscellaneous', typeFormattedText)
        ET.SubElement(miscElementUnused, 'p')
        createStringTypeElement(hazardBody, 'description', listToString(hazardData.get('description')))
        ET.SubElement(hazardBody, 'token', {'type' : 'token'})
        createStringTypeElement(hazardBody, 'name', hazardData.get('name'))
        createNumberTypeElement(hazardBody, 'level', hazardData.get('level'))
        createStringTypeElement(hazardBody, 'traits', listToString(hazardData.get('traits')))
        defensesDictionary = hazardData.get('defenses')
        if defensesDictionary:
            btElement = defensesDictionary.get('bt')
            hpElement = defensesDictionary.get('hp')
            hardnessElement = defensesDictionary.get('hardness')
            noteElement = defensesDictionary.get('notes')
            if hpElement:
                valuesList = hpElement.keys()
            createStringTypeElement(hazardBody, 'ac', acDictToString(defensesDictionary.get('ac')))
            if defensesDictionary.get('bt'):
                createNumberTypeElement(hazardBody, 'bt', defensesDictionary.get('bt').get('default'))
            if defensesDictionary.get('hp'):
                createNumberTypeElement(hazardBody, 'hp', defensesDictionary.get('hp').get('default'))
            hardnessString = ''
            for value in valuesList:
                hardnessNameString = value
                if value == 'default':
                    hardnessNameString = ''
                if hardnessElement:
                    hardnessString += hardnessNameString + ' Hardness ' + str(hardnessElement.get(value)) + ', '
                if hpElement:
                    hardnessString += hardnessNameString + ' HP ' + str(hpElement.get(value))
                if btElement:
                    hardnessString += ' (BT' + str(btElement.get(value)) + ') '
                if noteElement:
                    if type(noteElement) is str:
                        hardnessString += noteElement
                    else:
                        hardnessString += str(noteElement.get(value))
                hardnessString += '; '
            savingThrowDict = defensesDictionary.get('savingThrows')
            if savingThrowDict:
                createNumberTypeElement(hazardBody, 'fortitudesave', savingThrowDict.get('fort'))
                createNumberTypeElement(hazardBody, 'reflexsave', savingThrowDict.get('ref'))
                createNumberTypeElement(hazardBody, 'willsave', savingThrowDict.get('will'))
            createStringTypeElement(hazardBody, 'immunities', listToString(defensesDictionary.get('immunities')))
            createStringTypeElement(hazardBody, 'weaknesses', listToString(defensesDictionary.get('weaknesses')))
            createStringTypeElement(hazardBody, 'resistances', listToString(defensesDictionary.get('resistances')))
        createStringTypeElement(hazardBody, 'spelldisplaymode', 'action')
        createStringTypeElement(hazardBody, 'disable', entriesToString(hazardData.get('disable').get('entries')))
        createStringTypeElement(hazardBody, 'reset', listToString(hazardData.get('reset'), newline))
        createStringTypeElement(hazardBody, 'routine', entriesToString(hazardData.get('routine')))
        stealthDictionary = hazardData.get('stealth')
        initBonus = 0
        if stealthDictionary:
            stealthString = ''
            if stealthDictionary.get('bonus'):
                initBonus = stealthDictionary.get('bonus')
                stealthString += '+' + str(initBonus)
            if stealthDictionary.get('dc'):
                stealthString += 'DC ' + str(stealthDictionary.get('dc'))
            if stealthDictionary.get('minProf'):
                stealthString += ' (' + stealthDictionary.get('minProf') + ')'
            if stealthDictionary.get('notes'):
                stealthString += ' ' + stringFormatter(stealthDictionary.get('notes'))
            createStringTypeElement(hazardBody, 'stealth', stealthString)
        createNumberTypeElement(hazardBody, 'init', initBonus)
        actionsList = hazardData.get('actions')
        reactionsString = ''
        actionsString = ''
        rangedAttackString = ''
        meleeAttackString = ''
        if actionsList:
            for action in actionsList:
                if action.get('type') == 'ability':
                    if action.get('activity'):
                        reactionsString += ('' if len(reactionsString) == 0 else newline) + abilityToString(action)
                    else:
                        actionsString += ('' if len(actionsString) == 0 else newline) + abilityToString(action)
                elif action.get('type') == 'attack':
                    if action.get('range') == 'Ranged':
                        rangedAttackString += ('' if len(rangedAttackString) == 0 else newline) + attackStringFromAttacks([action], 'Ranged')
                    else:
                        meleeAttackString += ('' if len(meleeAttackString) == 0 else newline) + attackStringFromAttacks([action], 'Melee')
        createStringTypeElement(hazardBody, 'actions', actionsString)
        createStringTypeElement(hazardBody, 'meleeatk', meleeAttackString)
        createStringTypeElement(hazardBody, 'rangedatk', rangedAttackString)
        createStringTypeElement(hazardBody, 'reaction', reactionsString)
        id += 1

def writeDefinition(root, naming):
    nameBody = ET.SubElement(root, 'name')
    nameBody.text = naming
    categoryBody = ET.SubElement(root, 'category')
    authorBody = ET.SubElement(root, 'author')
    authorBody.text = 'Holo74'
    ruleSetBody = ET.SubElement(root, 'ruleset')
    ruleSetBody.text = 'PFRPG2'

def writeLibraryEntries(libraryEntry, displayName, name):
    libraryFeat = ET.SubElement(libraryEntry, name, staticModifier)
    libraryLink = ET.SubElement(libraryFeat, 'librarylink', {
                                'type': 'windowreference'})
    libraryClass = ET.SubElement(libraryLink, 'class')
    libraryClass.text = 'reference_list'
    recordName = ET.SubElement(libraryLink, 'recordname')
    recordName.text = '..'
    libraryType = ET.SubElement(libraryFeat, 'name', typeString)
    libraryType.text = displayName
    recordType = ET.SubElement(libraryFeat, 'recordtype', typeString)
    recordType.text = name

def zipping(db, definition, name):
    with zipfile.ZipFile(name + '.mod', 'w') as file:
        file.write(db)
    with zipfile.ZipFile(name + '.mod', 'a') as file:
        file.write(definition)
    print('Module Written')

def openGameLicenseStory(rootXML):
    licenseBody = ET.SubElement(rootXML, 'id-00001')
    nameBody = ET.SubElement(licenseBody, 'name', typeString)
    nameBody.text = 'OGL'
    textBody = ET.SubElement(licenseBody, 'text', typeFormattedText)
    heading = ET.SubElement(textBody, 'h')
    heading.text = 'Open Game License'
    preface = ET.SubElement(licenseBody, 'p')
    preface.text = 'The following text is the property of Wizards of the Coast, Inc. and is Copyright 2000 Wizards of the Coast, Inc ("Wizards"). All Rights Reserved.'
    with open('OGL.txt') as text:
        for line in text:
            body = ET.SubElement(textBody, 'p')
            body.text = line


def usageRequirementsStory(rootXML):
    licenseBody = ET.SubElement(rootXML, 'id-00002')
    nameBody = ET.SubElement(licenseBody, 'name', typeString)
    nameBody.text = 'Usage Requirements'
    textBody = ET.SubElement(licenseBody, 'text', typeFormattedText)
    heading = ET.SubElement(textBody, 'h')
    heading.text = 'This Fantasy Grounds library module uses trademarks'
    with open('UsageRequirement.txt') as text:
        for line in text:
            body = ET.SubElement(textBody, 'p')
            body.text = line

def writeDBFile():
    rootXML = ET.Element(
        'root', {'version': '4.1', 'dataversion': '20210708', 'release': '18|CoreRPG:4.1'})
    library = ET.SubElement(rootXML, 'library')
    modulesSubElement = ET.SubElement(library, 'pf2e_tools', {'static': 'true'})
    categoryName = ET.SubElement(modulesSubElement, 'categoryname', typeString)
    nameElement = ET.SubElement(modulesSubElement, 'name', typeString)
    nameElement.text = moduleName
    storyEntries = ET.SubElement(rootXML, 'encounter')

    openGameLicenseStory(storyEntries)
    usageRequirementsStory(storyEntries)

    createMonsterSpellList = True
    if os.path.exists('spells-sublist-data.json') == False:
        while os.path.exists('spells-sublist-data.json') == False:
            createSpellsInput = input('In order to parse the spells, you need the JSON File.  Would you like to skip the spells list? Y/n: ')
            if createSpellsInput == 'Y':
                createMonsterSpellList = False
            input('Please drop in the spells-sublist-data.json file and then press enter')
    else:
        if os.path.exists('bestiary-sublist-data.json'):
            createSpellsInput = input('Spell json detected.  Would you like to parse to the monsters spells list? Y/n: ')
            if createSpellsInput != 'Y':
                createMonsterSpellList = False
        else:
            createMonsterSpellList = False

    libraryEntries = ET.SubElement(modulesSubElement, 'entries')
    writeLibraryEntries(libraryEntries, 'Story', 'story')  

    if os.path.exists('feats-sublist-data.json'):
        if input('Parse Feats (Y)? ') == 'Y':
            writeFeatDBFile(rootXML)
            writeLibraryEntries(libraryEntries, 'Feats', 'feat')
    
    if os.path.exists('backgrounds-sublist-data.json'):
        if input('Parse Backgrounds (Y)? ') == 'Y':
            writeBackgrounds(rootXML)
            writeLibraryEntries(libraryEntries, 'Backgrounds', 'background')

    if os.path.exists('spells-sublist-data.json'):
        if input('Parse Spells (Y)? ') == 'Y':
            writeSpells(rootXML)
            writeLibraryEntries(libraryEntries, 'Spells', 'spell')

    npcElement = ''

    if os.path.exists('bestiary-sublist-data.json'):
        if input('Parse Monsters (Y)? ') == 'Y':
            npcElement = ET.SubElement(rootXML, 'npc')
            writeMonsters(npcElement, createMonsterSpellList)

    if os.path.exists('afflictions-sublist-data.json'):
        if input('Parse Afflictions (Y)? ') == 'Y':
            writeAfflictions(rootXML)
            writeLibraryEntries(libraryEntries, 'Afflictions', 'affliction')

    if os.path.exists('hazards-sublist-data.json'):
        if input('Parse Hazards (Y)? ') == 'Y':
            if type(npcElement) == str:
                npcElement = ET.SubElement(rootXML, 'npc')
            writeHazard(npcElement, npcElement)


    if type(npcElement) != str:
        writeLibraryEntries(libraryEntries, 'Bestiary', 'npc')

          
            

    tree = ET.ElementTree(rootXML)
    ET.indent(tree, '\t', level=0)

    with open('db.xml', 'wb') as files:
        ET.indent(rootXML, level=0)
        replaced = ET.tostring(rootXML, encoding='utf-8', method='xml', xml_declaration=True).replace(b'[a]&amp;', b'&')
        replaced = replaced.replace(b'&lt;', b'<')
        replaced = replaced.replace(b'&gt;', b'>')
        replaced = replaced.replace(b'[newline]', b'\n')
        files.write(replaced)

def writeDefinitionFile():
    rootXML = ET.Element(
        'root', {'version': '4.1', 'dataversion': '20210708', 'release': '18|CoreRPG:4.1'})

    writeDefinition(rootXML, moduleName)

    tree = ET.ElementTree(rootXML)
    ET.indent(tree, '\t', level=0)

    with open('definition.xml', 'wb') as files:
        tree.write(files, encoding='utf-8', xml_declaration=True)

def main():
    if not os.path.exists('OGL.txt'):
        print('Please have the Open Game License text within the folder')
        exit()

    if not os.path.exists('UsageRequirements.txt'):
        print('Please have the Usage Requirements text within the folder')

    print('By using this tool, you agree to the Usage Requirements')
    print('By using this tool, you agree to the OGL')
    agreement = input('Type N disagree and leave the tool: ')
    if agreement.upper() == 'N':
        print('thank you')
        exit()
    
    global moduleName 
    newName = input('Please enter a new name if you would like to change the current name (' + moduleName + ') to something different ')
    if len(newName) > 0:
        moduleName = str(newName)

    writeDBFile()
    writeDefinitionFile()

    zipping(os.path.relpath('db.xml'), os.path.relpath('definition.xml'), moduleName)

if __name__ == "__main__":
    main()