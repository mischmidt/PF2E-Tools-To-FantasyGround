import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile

moduleName = 'pf2e_tools'
typeString = {'type': 'string'}
typeFormattedText = {'type': 'formattedtext'}
typeNumber = {'type': 'number'}

def stringFormatter(s):
    if s is None:
        return ''
    entryRaw = s
    entrySafe = ''
    for split in re.split('{|}', entryRaw):
        parsing = split
        if re.search('(@as+)\s', parsing) is not None:
            actions = int(split[len(split) - 1])
            parsing = '[' + (actions * 'A') + ']'
        else:
            parsing = re.sub('@([a-zA-Z]+)\s', '', parsing)
            parsing = re.sub('\|(.+)', '', parsing)
        entrySafe += parsing
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
            output = '[a]&#14' + ('1' if activity.get('number') == 1 else str(activity.get('number') + 1)) + ';'
        else:
            output += (str)(activity.get('number'))
    if not isSymbol:
        output += unitType
    if unitType == 'reaction' and isSymbol:
        output = '[a]&#157;'
    if unitType == 'free':
        if isSymbol:
            output = '[a]&#129;'
        else:
            output += 'action'
    return output


def entriesToXML(parentXML, entries):
    for entry in entries:
        if type(entry) is not dict:
            baseEntry = ET.SubElement(parentXML, 'p')
            baseEntry.text = stringFormatter(entry)
        else:
            entryType = entry.get('type')
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
        keyword = ET.SubElement(successRate, 'b')
        keyword.text = stringFormatter(states)
        successRate.text = stringFormatter(success.get(states))


def listToXML(parentXML, list):
    root = ET.SubElement(parentXML, 'list')
    for item in list:
        bulletPoint = ET.SubElement(root, 'li')
        bulletPoint.text = stringFormatter(item)


def boldTextAndBody(parentXML, boldText, bodyText):
    bold = ET.SubElement(parentXML, 'h')
    bold.text = stringFormatter(boldText)
    root = ET.SubElement(parentXML, 'p')
    root.text = stringFormatter(bodyText)
    

def abilityToXML(parentXML, dictionary):
    titleField = ET.SubElement(parentXML, 'p')
    titleBolded = ET.SubElement(titleField, 'b')
    titleBolded.text = ''
    titleField.text = ''
    if 'name' in dictionary:
        titleBolded.text += stringFormatter(dictionary.get('name')) + ' '
    else:
        titleBolded.text = 'Activate'
    if 'activity' in dictionary:
        activity = activityToString(dictionary.get('activity'))
        titleBolded.text += activity + ' '
    if 'components' in dictionary:
        for component in dictionary.get('components'):
            titleField.text += stringFormatter(component) + ' '
    if 'traits' in dictionary:
        titleField.text += '['
        commaLock = True
        for trait in dictionary.get('traits'):
            if commaLock:
                commaLock = False
            else:
                titleField.text += ', '
            titleField.text += stringFormatter(trait).upper()
        titleField.text += ']'
    if 'requirements' in dictionary:
        boldTextAndBody(parentXML, 'Requirements', dictionary.get('requirements'))
    if 'trigger' in dictionary:
        boldTextAndBody(parentXML, 'Trigger', dictionary.get('trigger'))
    if 'frequency' in dictionary:
        boldTextAndBody(parentXML, 'Frequency', dictionary.get('frequency'))
    if 'entries' in dictionary:
        entriesToXML(parentXML, dictionary.get('entries'))

def optionListToString(optionsList):
    output = ''
    endLength = len(optionsList)
    for i in range(0, endLength):
        output += stringFormatter(optionsList[i])
        if i < endLength - 1:
            output += ', or '
    return output

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

        frequency = ET.SubElement(featBody, 'frequency', typeString)
        frequency.text = ''
        if 'frequency' in feat:
            frequency.text = stringFormatter(feat.get('frequency'))

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

    
def writeDefinition(root, naming):
    nameBody = ET.SubElement(root, 'name')
    nameBody.text = naming
    categoryBody = ET.SubElement(root, 'category')
    authorBody = ET.SubElement(root, 'author')
    authorBody.text = 'Holo74'
    ruleSetBody = ET.SubElement(root, 'ruleset')
    ruleSetBody.text = 'PFRPG2'

def writeLibraryEntries(libraryEntry, displayName, name):
    libraryFeat = ET.SubElement(libraryEntry, name)
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
    modulesSubElement = ET.SubElement(library, moduleName, {'static': 'true'})
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

    libraryEntries = ET.SubElement(library, 'entries')
    if os.path.exists('feats-sublist-data.json'):
        writeLibraryEntries(libraryEntries, 'Feats', 'feat')
    
    if os.path.exists('backgrounds-sublist-data.json'):
        writeLibraryEntries(libraryEntries, 'Backgrounds', 'background')

    tree = ET.ElementTree(rootXML)
    ET.indent(tree, '\t', level=0)

    with open('db.xml', 'wb') as files:
        ET.indent(rootXML, level=0)
        replaced = ET.tostring(rootXML, encoding='utf-8', method='xml', xml_declaration=True).replace(b'[a]&amp;', b'&')
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
    
    writeDBFile()
    writeDefinitionFile()

    zipping(os.path.relpath('db.xml'), os.path.relpath('definition.xml'), moduleName)

if __name__ == "__main__":
    main()