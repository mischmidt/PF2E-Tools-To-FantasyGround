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
    if entryType == 'successDegree':
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
            output += numbersToWordNumber[frequency.get('freq')]
        if frequency.get('unit'):
            output += ' per ' + frequency.get('unit')
    return output

def monsterAbilityToXML(parentXML, dictionary, number):
    bodyElement = ET.SubElement(parentXML, f'id-{number:05}')
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
        newLineCharacter = '[newline]'
    if 'requirements' in dictionary:
        descriptionString += newLineCharacter + '- Requirements: ' + dictionary.get('requirements')
        newLineCharacter = '[newline]'
    if 'trigger' in dictionary:
        descriptionString += newLineCharacter + '- Trigger: ' + dictionary.get('trigger')
        newLineCharacter = '[newline]'
    if 'frequency' in dictionary:
        descriptionString += newLineCharacter + '- Frequency: ' + frequencyToString(dictionary.get('frequency'))
        newLineCharacter = '[newline]'
    if 'entries' in dictionary:
        holding = ET.Element('body')
        entriesToXML(holding, dictionary.get('entries'))
        ET.indent(holding, level=0, space='')
        arrayHolder = ET.tostringlist(holding, 'unicode', 'text')
        for ability in arrayHolder:
            if ability == '\n':
                continue
            descriptionString += newLineCharacter + ability
    createStringTypeElement(bodyElement, 'name', nameString)
    createStringTypeElement(bodyElement, 'desc', descriptionString)

def optionListToString(optionsList):
    output = ''
    endLength = len(optionsList)
    for i in range(0, endLength):
        output += stringFormatter(optionsList[i])
        if i < endLength - 1:
            output += ', or '
    return output

def listToString(list):
    output = ''
    if list is None:
        return ''
    endLength = len(list)
    for i in range(0, endLength):
        output += stringFormatter(list[i])
        if i < endLength - 1:
            output += ',  '
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


def writeSpells(rootXML):
    file = open('spells-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    spellElement = ET.SubElement(rootXML, 'spell')
    category = ET.SubElement(spellElement, 'category', {'name': moduleName})
    for spell in data:
        spellBody = ET.SubElement(category, f'id-{id:05}')
        createStringTypeElement(spellBody, 'name', spell.get('name'))
        createStringTypeElement(spellBody, 'source', spell.get('source'))
        createStringTypeElement(spellBody, 'spelltype', spell.get('type').upper())
        createStringTypeElement(spellBody, 'spelltypelabel', spell.get('type')[0])
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
        if attack.get('range') != attackType:
            continue
        if multipleMeleeLock:
            attackString += '[newline]'
        attackString += actionParser['1'] + ' '
        attackString += stringFormatter(attack.get('name'))
        attackString += ' +' + str(attack.get('attack'))
        attackString += ' (' + listToString(attack.get('traits')) + '), Damage '
        attackString += stringFormatter(attack.get('damage')) + ' '
        if len(attack.get('effects')) > 0:
            attackString += 'plus ' + listToString(attack.get('effects'))
        multipleMeleeLock = True
    return attackString

def spellEntriesToString(entries):
    output = ''
    spellLock = False
    if entries is None:
        return ''
    for spell in entries:
        if spellLock:
            output += '[newline]'
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

def writeMonsters(rootXML):
    file = open('bestiary-sublist-data.json')
    data = json.load(file)
    file.close()
    id = 1
    beastElement = ET.SubElement(rootXML, 'npc')
    category = ET.SubElement(beastElement, 'category', {'name': moduleName})
    for beast in data:
        beastBody = ET.SubElement(category, f'id-{id:05}')
        acText = ''
        if beast.get('ac') is not None:
            acText += str(beast.get('ac').get('default'))
            for acEntries in beast.get('ac'):
                if acEntries == 'default' or acEntries == 'abilities':
                    continue
                acText += ' (' + str(beast.get('ac').get(acEntries)) + ' ' + acEntries + ' ' + ')'
            acAbilities = beast.get('ac').get('abilities')
            if acAbilities is not None:
                acText += '; ' + acAbilities + ';'
        createStringTypeElement(beastBody, 'ac', acText)
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
        immunitiesString = ''
        immunity = beast.get('immunities')
        if immunity is not None:
            immunities = []
            if immunity.get('damage') is not None:
                immunities.extend(immunity.get('damage'))
            if immunity.get('condition') is not None:
                immunities.extend(immunity.get('condition'))
            immunitiesString = listToString(immunities)
        createStringTypeElement(beastBody, 'immunities', immunitiesString)
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
        emptyBodyTextElement = ET.SubElement(textElement, 'p')
        tokenElement = ET.SubElement(beastBody, 'token', {'type' : 'token'})
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
        genericSpellString = ''
        if beast.get('spellcasting') is not None:
            for spellCasting in beast.get('spellcasting'):
                if spellCasting.get('type') == 'Innate':
                    innateSpellString += spellFromSpellCasting(spellCasting)
                elif spellCasting.get('type') == 'Focus':
                    focusSpellString += spellFromSpellCasting(spellCasting)
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
                    ritualString += '[newline]'
                if ritual.get('tradition') is not None:
                    ritualString += ritual.get('tradition') + ' Rituals '
                if ritual.get('DC') is not None:
                    ritualString += 'DC ' + str(ritual.get('DC'))
                ritualString += spellListToString(ritual.get('rituals'))

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

    if os.path.exists('feats-sublist-data.json'):
        writeFeatDBFile(rootXML)
    
    if os.path.exists('backgrounds-sublist-data.json'):
        writeBackgrounds(rootXML)

    if os.path.exists('spells-sublist-data.json'):
        writeSpells(rootXML)

    if os.path.exists('bestiary-sublist-data.json'):
        writeMonsters(rootXML)

    libraryEntries = ET.SubElement(modulesSubElement, 'entries')
    writeLibraryEntries(libraryEntries, 'Story', 'story')
    if os.path.exists('feats-sublist-data.json'):
        writeLibraryEntries(libraryEntries, 'Feats', 'feat')
    
    if os.path.exists('backgrounds-sublist-data.json'):
        writeLibraryEntries(libraryEntries, 'Backgrounds', 'background')
    
    if os.path.exists('spells-sublist-data.json'):
        writeLibraryEntries(libraryEntries, 'Spells', 'spell')
    
    if os.path.exists('bestiary-sublist-data.json'):
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