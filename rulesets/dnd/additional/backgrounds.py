from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Background:
    key: str
    label: str
    skills: tuple
    tools: tuple = ()
    languages: int = 0
    equipment: tuple = ()
    feature: tuple = ("", "")
    traits: tuple = ()
    ideals: tuple = ()
    bonds: tuple = ()
    flaws: tuple = ()
    detail: str = ""


BACKGROUNDS = {
    "acolyte": Background(
        "acolyte", "Acolyte", ("insight", "religion"), languages=2,
        equipment=("a holy symbol", "a prayer book", "5 sticks of incense", "vestments", "15 gp"),
        feature=("Shelter of the Faithful",
                 "You and your companions can expect free healing and care at temples of your faith, "
                 "and you can call on priests for aid and shelter."),
        traits=("I idolize a particular hero of my faith and constantly refer to their deeds.",
                "I can find common ground between the fiercest enemies, empathizing with them.",
                "I've spent so long in the temple that I have little practical experience with the world.",
                "I quote (or misquote) sacred texts in almost every situation."),
        ideals=("Faith. I trust that my deity will guide my actions. (Lawful)",
                "Charity. I always try to help those in need, no matter the personal cost. (Good)"),
        bonds=("I would die to recover an ancient relic of my faith that was lost long ago.",
               "I seek to preserve a sacred text that my enemies seek to destroy."),
        flaws=("I judge others harshly, and myself even more severely.",
               "I put too much trust in those who wield power within my temple's hierarchy."),
        detail="Servant of a temple; free care at shrines of your faith."),
    "charlatan": Background(
        "charlatan", "Charlatan", ("deception", "sleight_of_hand"),
        tools=("disguise kit", "forgery kit"),
        equipment=("fine clothes", "a disguise kit", "tools of your con of choice", "15 gp"),
        feature=("False Identity",
                 "You have a second, documented identity, and you can forge papers and mimic "
                 "handwriting once you've seen a sample."),
        traits=("I fall in and out of love easily, and am always pursuing someone.",
                "I have a joke for every occasion, especially occasions where humor is inappropriate.",
                "Flattery is my preferred trick for getting what I want."),
        ideals=("Independence. I am a free spirit -- no one tells me what to do. (Chaotic)",
                "Fairness. I never target people who can't afford to lose a few coins. (Lawful)"),
        bonds=("I fleeced the wrong person and must work to ensure they never cross my path again.",
               "I owe everything to my mentor, a horrible person who's probably rotting in jail."),
        flaws=("I can't resist swindling people who are more powerful than I am.",
               "I'm convinced no one could ever fool me the way I fool others."),
        detail="A con artist with a forged second identity."),
    "criminal": Background(
        "criminal", "Criminal", ("deception", "stealth"),
        tools=("thieves' tools", "one gaming set"),
        equipment=("a crowbar", "dark common clothes with a hood", "15 gp"),
        feature=("Criminal Contact",
                 "You have a reliable contact in the criminal underworld and know how to get "
                 "messages to and from them, even across distances."),
        traits=("I always have a plan for what to do when things go wrong.",
                "The first thing I do in a new place is note the locations of valuables.",
                "I would rather make a new friend than a new enemy."),
        ideals=("Honor. I don't steal from others in the trade. (Lawful)",
                "Freedom. Chains are meant to be broken, as are those who would forge them. (Chaotic)"),
        bonds=("I'm trying to pay off an old debt I owe to a generous benefactor.",
               "Someone I loved died because of a mistake I made -- that will never happen again."),
        flaws=("When I see something valuable, I can't think about anything but how to steal it.",
               "I turn tail and run when things look bad."),
        detail="A thief or scoundrel with an underworld contact."),
    "folk_hero": Background(
        "folk_hero", "Folk Hero", ("animal_handling", "survival"),
        tools=("one artisan's tools", "vehicles (land)"),
        equipment=("artisan's tools", "a shovel", "an iron pot", "common clothes", "10 gp"),
        feature=("Rustic Hospitality",
                 "Common folk shelter and hide you from the law or anyone searching for you, "
                 "so long as you don't put them in danger."),
        traits=("I judge people by their actions, not their words.",
                "If someone is in trouble, I'm always ready to lend help.",
                "I'm confident in my own abilities and do what I can to instill confidence in others."),
        ideals=("Sincerity. There's no good in pretending to be something I'm not. (Neutral)",
                "Justice. I help those who can't help themselves, no matter the cost. (Good)"),
        bonds=("I have a family, but I have no idea where they are -- one day I hope to see them again.",
               "I worked the land, I love the land, and I will protect the land."),
        flaws=("The tyrant who rules my land will stop at nothing to see me killed.",
               "I have a weakness for the vices of the city, especially hard drink."),
        detail="A commoner risen to local legend by a defining deed."),
    "guild_artisan": Background(
        "guild_artisan", "Guild Artisan", ("insight", "persuasion"),
        tools=("one artisan's tools",), languages=1,
        equipment=("artisan's tools", "a letter of introduction from your guild", "traveler's clothes", "15 gp"),
        feature=("Guild Membership",
                 "Your guild provides lodging and food, political clout, and aid from fellow members; "
                 "you pay dues and the guild backs you in disputes."),
        traits=("I believe anything worth doing is worth doing right -- I can be a bit of a perfectionist.",
                "I'm well known for my work, and I want to make sure everyone appreciates it.",
                "I always want to know how things work and what makes people tick."),
        ideals=("Community. It is the duty of all civilized people to strengthen the bonds of society. (Lawful)",
                "Aspiration. I work hard to be the best there is at my craft. (Any)"),
        bonds=("The workshop where I learned my trade is the most important place in the world to me.",
               "I owe my guild a great debt for forging me into the person I am today."),
        flaws=("I'm horribly jealous of anyone who can outshine my handiwork.",
               "I'm never satisfied with what I have -- I always want more."),
        detail="A skilled crafter backed by a powerful guild."),
    "hermit": Background(
        "hermit", "Hermit", ("medicine", "religion"),
        tools=("herbalism kit",), languages=1,
        equipment=("a scroll case of notes", "a winter blanket", "an herbalism kit", "5 gp"),
        feature=("Discovery",
                 "In your seclusion you found a unique and powerful truth -- a secret, a relic's "
                 "location, a portent -- whose significance the DM helps define."),
        traits=("I've been isolated for so long that I rarely speak, preferring gestures and grunts.",
                "I am utterly serene, even in the face of disaster.",
                "I connect everything that happens to me to a grand cosmic plan."),
        ideals=("Greater Good. My gifts are meant to be shared with all, not hoarded. (Good)",
                "Self-Knowledge. If you know yourself, there's nothing left to know. (Any)"),
        bonds=("Nothing is more important than the other members of my hermitage, order, or family.",
               "I entered seclusion to hide from the ones who might still be hunting me."),
        flaws=("Now that I've returned to the world, I enjoy its delights a little too much.",
               "I harbor dark, bloodthirsty thoughts that my isolation failed to quell."),
        detail="A recluse returned from seclusion with a discovery."),
    "noble": Background(
        "noble", "Noble", ("history", "persuasion"),
        tools=("one gaming set",), languages=1,
        equipment=("fine clothes", "a signet ring", "a scroll of pedigree", "25 gp"),
        feature=("Position of Privilege",
                 "People are inclined to think the best of you; you're welcome in high society and "
                 "can secure audiences with local nobles."),
        traits=("My eloquent flattery makes everyone I talk to feel like the most wonderful person.",
                "Despite my noble birth, I do not place myself above other folk -- we all have the same blood.",
                "I take great pains to always look my best and follow the latest fashions."),
        ideals=("Responsibility. It is my duty to respect the authority of those above me. (Lawful)",
                "Noble Obligation. It is my duty to protect and care for the people beneath me. (Good)"),
        bonds=("I will face any challenge to win the approval of my family.",
               "The common folk must see me as a hero of the people."),
        flaws=("I secretly believe that everyone is beneath me.",
               "I have an insatiable desire for carnal pleasures and luxuries."),
        detail="Highborn, with wealth, a title, and social clout."),
    "outlander": Background(
        "outlander", "Outlander", ("athletics", "survival"),
        tools=("one musical instrument",), languages=1,
        equipment=("a staff", "a hunting trap", "a trophy from a slain animal", "traveler's clothes", "10 gp"),
        feature=("Wanderer",
                 "You have an excellent memory for geography and can always recall the general layout "
                 "of terrain, settlements, and features; you can find food and water for your party."),
        traits=("I'm driven by a wanderlust that led me away from home.",
                "I have a lesson for every situation, drawn from observing nature.",
                "I place no stock in wealthy or well-mannered folk -- money and manners won't save you."),
        ideals=("Nature. The natural world is more important than the constructs of civilization. (Neutral)",
                "Glory. I must earn glory in battle, for myself and my clan. (Any)"),
        bonds=("My family, clan, or tribe is the most important thing in my life.",
               "I suffer awful visions of a coming disaster and will do anything to prevent it."),
        flaws=("I am too enamored of ale, wine, and other intoxicants.",
               "Violence is my answer to almost any challenge."),
        detail="Raised in the wilds, far from civilization."),
    "sage": Background(
        "sage", "Sage", ("arcana", "history"), languages=2,
        equipment=("a bottle of ink", "a quill", "a small knife", "a letter from a dead colleague", "10 gp"),
        feature=("Researcher",
                 "When you don't know something, you usually know where and from whom to find it -- "
                 "a library, a scholar, or another reliable source."),
        traits=("I use polysyllabic words that convey the impression of great erudition.",
                "I've read every book in the world's greatest libraries -- or I like to boast that I have.",
                "I am horribly, horribly awkward in social situations."),
        ideals=("Knowledge. The path to power and self-improvement is through knowledge. (Neutral)",
                "Beauty. What is beautiful points us beyond itself toward what is true. (Good)"),
        bonds=("It is my duty to protect my students.",
               "I work to preserve a library, university, scriptorium, or monastery."),
        flaws=("I am easily distracted by the promise of information.",
               "Most people scream and run when they see a demon -- I stop and take notes."),
        detail="A scholar with deep, specialized learning."),
    "sailor": Background(
        "sailor", "Sailor", ("athletics", "perception"),
        tools=("navigator's tools", "vehicles (water)"),
        equipment=("a belaying pin (club)", "50 feet of silk rope", "a lucky charm", "common clothes", "10 gp"),
        feature=("Ship's Passage",
                 "You can secure free passage on a sailing ship for yourself and companions, working "
                 "your way across, thanks to your reputation among sailors."),
        traits=("My friends know they can rely on me, no matter what.",
                "I work hard so that I can play hard when the work is done.",
                "I never pass up a friendly wager."),
        ideals=("Freedom. The sea is freedom -- the freedom to go anywhere and do anything. (Chaotic)",
                "Mastery. I'm a predator, and the other ships on the sea are my prey. (Evil)"),
        bonds=("I'm loyal to my captain first; everything else comes second.",
               "The ship is most important -- crewmates and captains come and go."),
        flaws=("I follow orders, even if I think they're wrong.",
               "I'll say anything to avoid having to do extra work."),
        detail="A deckhand at home on the open water."),
    "soldier": Background(
        "soldier", "Soldier", ("athletics", "intimidation"),
        tools=("one gaming set", "vehicles (land)"),
        equipment=("an insignia of rank", "a trophy from a fallen enemy", "a deck of cards", "common clothes", "10 gp"),
        feature=("Military Rank",
                 "Soldiers loyal to your former organization recognize your rank; you can invoke it to "
                 "gain access, requisition simple equipment, and command lower-ranked soldiers."),
        traits=("I'm always polite and respectful, a habit from my time in the ranks.",
                "I can stare down a hell hound without flinching.",
                "I face problems head-on -- a simple, direct solution is the best path to success."),
        ideals=("Greater Good. Our lot is to lay down our lives in defense of others. (Good)",
                "Responsibility. I do what I must and obey just authority. (Lawful)"),
        bonds=("I would still lay down my life for the people I served with.",
               "My honor is my life -- without it, I am nothing."),
        flaws=("The monstrous enemy we faced in battle still leaves me quivering with fear.",
               "I obey the law, even if the law causes misery."),
        detail="A veteran of an army or martial company."),
    "urchin": Background(
        "urchin", "Urchin", ("sleight_of_hand", "stealth"),
        tools=("disguise kit", "thieves' tools"),
        equipment=("a small knife", "a map of your home city", "a pet mouse", "a token of your parents", "10 gp"),
        feature=("City Secrets",
                 "You know the secret patterns and flow of cities and can find passages through the "
                 "urban sprawl, moving between locations twice as fast as normal."),
        traits=("I hide scraps of food and trinkets away in my pockets.",
                "I ask a lot of questions.",
                "I sleep with my back to a wall or tree, with everything I own wrapped in a bundle."),
        ideals=("Respect. All people deserve to be treated with dignity. (Good)",
                "Independence. When people follow orders blindly, they embrace a kind of tyranny. (Chaotic)"),
        bonds=("My town or city is my home, and I'll fight to defend it.",
               "I owe my survival to another urchin who taught me to live on the streets."),
        flaws=("If there's a plan, I'll forget it -- if I don't forget it, I'll ignore it.",
               "I will never fully trust anyone other than myself."),
        detail="A street child who survived on wit and theft."),
}

ORDER = ("acolyte", "charlatan", "criminal", "entertainer", "folk_hero", "guild_artisan",
         "hermit", "noble", "outlander", "sage", "sailor", "soldier", "urchin")
ORDER = tuple(k for k in ORDER if k in BACKGROUNDS)


def get(key: str) -> Background | None:
    return BACKGROUNDS.get((key or "").lower())


def roleplay_seed(bg: Background) -> dict:
    return {
        "background": bg.label,
        "feature": {"name": bg.feature[0], "text": bg.feature[1]},
        "suggested_traits": list(bg.traits),
        "suggested_ideals": list(bg.ideals),
        "suggested_bonds": list(bg.bonds),
        "suggested_flaws": list(bg.flaws),
    }
