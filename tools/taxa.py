"""Hand-curated metadata used for difficulty levels."""
GENUS_FAMILY = {}
def _f(fam, *genera):
    for g in genera: GENUS_FAMILY[g] = fam
_f("Cardinals & allies","Cardinalis","Pheucticus","Passerina","Piranga")
_f("Jays & crows","Cyanocitta","Aphelocoma","Pica","Nucifraga","Perisoreus","Corvus")
_f("Thrushes","Turdus","Sialia","Catharus","Hylocichla","Ixoreus")
_f("Finches","Spinus","Haemorhous","Coccothraustes","Loxia","Pinicola")
_f("Chickadees & titmice","Poecile","Baeolophus")
_f("Nuthatches & creepers","Sitta","Certhia")
_f("Woodpeckers","Dryobates","Leuconotopicus","Melanerpes","Dryocopus","Colaptes","Sphyrapicus")
_f("Pigeons & doves","Zenaida","Columba","Streptopelia")
_f("Mimids","Mimus","Dumetella","Toxostoma")
_f("Waxwings","Bombycilla"); _f("Starlings","Sturnus"); _f("Old World sparrows","Passer")
_f("New World sparrows","Melospiza","Zonotrichia","Junco","Spizella","Pipilo")
_f("Blackbirds & orioles","Agelaius","Molothrus","Quiscalus","Icterus","Sturnella","Dolichonyx")
_f("Wrens","Thryothorus","Troglodytes","Cistothorus","Campylorhynchus")
_f("Kinglets","Regulus","Corthylio")
_f("Hummingbirds","Archilochus","Calypte","Selasphorus")
_f("Swallows & swifts","Hirundo","Tachycineta","Progne","Chaetura")
_f("Tyrant flycatchers","Sayornis","Tyrannus","Pyrocephalus","Myiarchus")
_f("Warblers","Setophaga","Geothlypis","Mniotilta","Seiurus")
_f("Buntings & larks","Plectrophenax","Eremophila")
_f("Kingfishers","Megaceryle")
_f("Herons & egrets","Ardea","Egretta","Butorides","Nycticorax","Botaurus")
_f("Cranes","Antigone","Grus")
_f("Ibises, storks & spoonbills","Mycteria","Platalea","Eudocimus")
_f("Pelicans & cormorants","Pelecanus","Nannopterum","Anhinga")
_f("Ducks, geese & swans","Branta","Anser","Anas","Aix","Spatula","Bucephala","Mergus","Lophodytes","Aythya","Cygnus")
_f("Loons & grebes","Gavia","Podilymbus")
_f("Rails & coots","Fulica")
_f("Shorebirds","Charadrius","Recurvirostra","Actitis","Arenaria","Calidris","Tringa","Scolopax")
_f("Gulls, terns & skimmers","Leucophaeus","Larus","Hydroprogne","Rynchops")
_f("Auks & gannets","Fratercula","Uria","Morus")
_f("Eagles, hawks & ospreys","Haliaeetus","Aquila","Pandion","Buteo","Astur","Accipiter","Circus")
_f("Falcons","Falco")
_f("Vultures & condors","Cathartes","Coragyps","Gymnogyps")
_f("Owls","Bubo","Strix","Megascops","Tyto","Athene")
_f("Game birds","Meleagris","Bonasa","Callipepla","Phasianus")
_f("Cuckoos & nightjars","Geococcyx","Chordeiles")
_f("Dippers","Cinclus")

# Easy mode: familiar backyard / everyday birds (by common name)
EASY = set("""Northern Cardinal|Blue Jay|American Robin|American Goldfinch|House Finch|Black-capped Chickadee|
Tufted Titmouse|White-breasted Nuthatch|Downy Woodpecker|Pileated Woodpecker|Northern Flicker|Mourning Dove|
Rock Pigeon|Northern Mockingbird|Eastern Bluebird|European Starling|House Sparrow|Song Sparrow|Dark-eyed Junco|
Red-winged Blackbird|Common Grackle|Baltimore Oriole|American Crow|Common Raven|Carolina Wren|
Ruby-throated Hummingbird|Barn Swallow|Mallard|Canada Goose|Mute Swan|Bald Eagle|Red-tailed Hawk|Osprey|
Great Blue Heron|Turkey Vulture|Great Horned Owl|Snowy Owl|Wild Turkey|Atlantic Puffin|Herring Gull|
Brown Pelican|Belted Kingfisher|Peregrine Falcon|Barn Owl|Cedar Waxwing|Wood Duck|Sandhill Crane|
Roseate Spoonbill|Painted Bunting|Greater Roadrunner|Steller's Jay|Anna's Hummingbird""".replace("\n","").split("|"))
