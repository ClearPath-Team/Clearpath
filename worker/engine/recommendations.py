"""Track M2: Curated Romanian recommendation templates for WCAG violations detected by axe-core."""

RECOMMENDATIONS = {
    "input-image-alt": (
        "Butonul imagine nu are nume accesibil",
        "Adaugă un atribut alt care descrie acțiunea butonului imagine."
    ),
    "select-name": (
        "Lista derulantă nu are etichetă",
        "Asociază un element <label> sau un atribut aria-label listei derulante."
    ),
    "page-has-heading-one": (
        "Pagina nu are un titlu principal",
        "Adaugă un element <h1> care descrie subiectul principal al paginii."
    ),
    "landmark-one-main": (
        "Pagina nu are un reper pentru conținutul principal",
        "Încadrează conținutul principal într-un element <main>."
    ),
    "region": (
        "Conținutul nu aparține unui reper de pagină",
        "Organizează conținutul în repere precum <main>, <nav>, <header> și <footer>."
    ),
    "list": (
        "Lista conține elemente cu structură incorectă",
        "Folosește elemente <li> pentru intrările directe din <ul> sau <ol>."
    ),
    "listitem": (
        "Elementul de listă nu aparține unei liste",
        "Plasează elementul <li> într-un element <ul> sau <ol>."
    ),
    "aria-hidden-focus": (
        "Un element ascuns cititorului de ecran poate primi focalizarea",
        "Elimină aria-hidden de pe elementul interactiv sau exclude-l din ordinea de focalizare."
    ),
    "nested-interactive": (
        "Elementele interactive sunt imbricate",
        "Separă butoanele, linkurile și celelalte controale interactive în elemente independente."
    ),
    "frame-title": (
        "Cadrul nu are un titlu accesibil",
        "Adaugă un atribut title descriptiv elementului <iframe> sau <frame>."
    ),
    "duplicate-id-aria": (
        "Referințele ARIA folosesc identificatori duplicați",
        "Folosește identificatori id unici și actualizează atributele ARIA care îi referă."
    ),
    "button-name": (
        "Butonul nu are nume accesibil",
        "Adaugă un text vizibil sau un atribut aria-label care descrie acțiunea butonului."
    ),
    "image-alt": (
        "Imaginea nu are atribut alt",
        "Adaugă un atribut alt care descrie scopul sau conținutul imaginii."
    ),
    "label": (
        "Câmpul de formular nu are etichetă",
        "Asociază un element <label for=\"id\"> sau un atribut aria-label câmpului."
    ),
    "keyboard-trap": (
        "Capcană de tastatură: utilizatorul nu mai poate ieși cu Tab",
        "Nu intercepta tasta Tab. Utilizatorul trebuie să poată ajunge la elementul următor fără mouse."
    ),
    "link-name": (
        "Linkul nu are text discernibil",
        "Adaugă un text vizibil sau aria-label pentru a descrie destinația linkului."
    ),
    "html-has-lang": (
        "Elementul html nu are atribut lang",
        "Adaugă atributul lang pe tag-ul <html> (de exemplu <html lang=\"ro\">)."
    ),
    "color-contrast": (
        "Contrast insuficient între text și fundal",
        "Mărește contrastul textului pentru a atinge raportul minim WCAG de 4.5:1."
    ),
    "heading-order": (
        "Ordinea nivelurilor de titlu este incorectă",
        "Structurați titlurile ierarhic fără a sări peste niveluri (de exemplu de la h1 direct la h4)."
    ),
    "document-title": (
        "Pagina nu are titlu document",
        "Adaugă un element <title> descriptiv în interiorul tag-ului <head>."
    ),
    "empty-heading": (
        "Titlu fără conținut",
        "Asigură-te că fiecare element de titlu conține text descriptiv."
    ),
}
