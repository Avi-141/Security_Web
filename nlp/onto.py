import pronto

ms = pronto.Ontology("https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo")

keyword = "sample state"
keyword = keyword.split()
similarity = 0
syn_onto = "-1"
synonyms = []

for term in ms:
    s=term.name
    s=s.split()
    sm = 0
    for w2 in s:
        simi = 0
        for keys in keyword:
            try:
                simi = max(model.wv.similarity(keys,w2),simi)
            except:
                if keys == w2:
                    simi = 1.0
                else:
                    # can use edit distance for word similarity: ED/2*Max(Words' length)
                    pass    
        sm += simi
    if sm > similarity:
        synonyms = []
        synonyms.append(term.name)
        similarity = sm
    elif sm == similarity:
        synonyms.append(term.name)


# print (synonyms)


children_array = []

for word in synonyms:
    for term in ms:
        if word == term.name and term.children:
            children_array += term.children.name

for word in children_array:
    for term in ms:
        if word == term.name and term.children:
            # directly adding children of children to synonyms
            synonyms.append(term.children.name)
            
synonyms += children_array

# print (children_array)
print (synonyms)