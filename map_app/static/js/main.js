
     // Coordenadas del polígono de la Ciudad de México
     const mexicoCityBounds = [
        [18.973773, -99.316406], // Suroeste
        [19.592757, -98.940308] // Noreste
    ];

    // Inicializar el mapa centrado en la Ciudad de México
    const map = L.map('map', {
        //crs: L.CRS.EPSG3857,  //funcion que puede no funcionar 
        center: [19.432608, -99.133209], // Centro de la Ciudad de México
        zoom: 12, // Zoom inicial
        zoomControl: false,
        minZoom: 11, // Zoom mínimo
        maxZoom: 19, // Zoom máximo 16
        maxBounds: mexicoCityBounds, // Limitar el mapa a la Ciudad de México
        maxBoundsViscosity: 1.0 // Evitar que se salga del límite
    });

    // Capas de mapas
    //https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}  base esriworld
    const layers = {
        topographic: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Datos: Google',
            maxZoom: 20
        }),
        satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
            attribution: 'Datos: Google',
            maxZoom: 20
        }),

        openstreet: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
            attribution: 'Datos:Google',
            maxZoom:20
        })
    };

    // Agregar la capa inicial
 
    // Cargar los polígonos al iniciar la página
    loadPolygons();
    // Dibujar el polígono de la Ciudad de México (opcional, para visualización)
    
    layers.topographic.addTo(map);
    

    function Busqueda(){
        const tipo=document.querySelector('input[name="tipo-busqueda"]:checked').value;
        if(tipo==="construccion"){
            buscarPredioGlobal();

        }else {
            buscarPredioGlobal();
        }
    }

    function actualizarPlaceholder(){
        const input=document.getElementById('input-predio-global');
        const tipo=document.querySelector('input[name="tipo-busqueda"]:checked').value;
        input.placeholder=tipo==="construccion"
        ?"Clave de construccion (Ej: 07668901)"
        :"Clave de predio (Ej: 092383)"
    }

    function validarInput(){
        const input=document.getElementById('input-predio-global');
        const tooltip=document.querySelector('.tooltip');
        if (input.value.length  !==8){
            tooltip.style.display  ='block';
            return false;
        }
        tooltip.style.display='none';
        return true;
    }

    function handleEnter(event){
        if(event.key === 'Enter'){
            Busqueda();
        }
    }

    
    function loadPolygons() {
      fetch('/get_polygons')
       .then(response => response.json())
       .then(data => {
        // Agregar los polígonos al mapa con tooltips
        L.geoJSON(data, {
            style: {
                color: '#800000',
                weight: 2,
                fillColor: 'bd6568',
                fillOpacity: 0.2
            },
            onEachFeature: function(feature, layer) {
                // Verificar si la propiedad "nombre_delegacion" existe en el feature
                if (feature.properties && feature.properties.NOMGEO) {
                    // Agregar un tooltip con el nombre de la delegación
                    layer.bindTooltip(feature.properties.NOMGEO, {
                        permanent: false, // El tooltip no es permanente (solo se muestra al pasar el mouse)
                        direction: 'top', // Dirección del tooltip
                        className: 'custom-tooltip' // Clase CSS personalizada (opcional)
                    });
                }
            }
        }).addTo(map);
        })
       .catch(error => console.error('Error al cargar los polígonos:', error));
       }

    //funcion para agregar delegaciones y demas capas //id="tipo-busqueda"
    let delegacionLayer = null; // Almacenar la capa actual   "mostrarFormulario('${delegacion}', this.value)"
    let marcadoresLayer =null;
    function mostrarOpciones(delegacion) {
        //const busquedaGlobal=document.getElementById("busqueda-global")
        //if (delegacion){
          //  busquedaGlobal.style.display="none";
        //} else if(!delegacion){
          //  busquedaGlobal.style.display = "block";
        //}
        
        const opcionesHTML = `     
            <select id="delegaciones" title="opciones de busqueda" onchange="mostrarFormulario('${delegacion}', this.value)">  
            <option value="val" title="Elige una opcion de busqueda">Opciones de búsqueda</option>
            <option value="colonia" title="Busca por numero de colonia">Por Colonia</option>
            <option value="manzana" title="Busca por clave  de manazana">Por Manzana</option>
            <option value="predio" title="Buca por fid de predio">Por Predio</option>
            <option value="construccion">Construcción</option>
            <option value="segmentacion" title="segmentacion del valor de suelo de predio 1-4">Segmentacion valor de suelo</option>
            </select>`;
        document.getElementById('opciones-container').innerHTML = opcionesHTML;
        document.getElementById('formulario-container').innerHTML = '';}

  

    
        //funcion para mostrar el formulario    mostrarFormulario(delegacion, tipo)
    function mostrarFormulario(delegacion, tipo) {
        const placeholders = {
            'val': 'Elige una opcion de busqueda',
           'colonia': 'No.de Colonia Ej:001',
           'manzana':'Clave de la Manzana Ej: 076123',
           'predio': 'fid  de predio Ej:07768901',
           'construccion': 'fid de construccion Ej: 383838',
           'segmentacion':'ingresa un numero entre 1 y 10 '};

        const formularioHTML = `
            <div class="form-group">
                <input type="text" 
                    placeholder="${placeholders[tipo]}" 
                    id="input-busqueda"
                    class="search-input"
                    onkeypress="manejarEnter(event,'${delegacion}','${tipo}')">
                <button onclick="realizarBusqueda('${delegacion}', '${tipo}')" class="search-button"> Buscar </button>
            </div>`;

        document.getElementById('formulario-container').innerHTML = formularioHTML;} 
    
    function manejarEnter(event,delegacion,tipo){
        if(event.key === 'Enter' || event.keyCode === 13){
            realizarBusqueda(delegacion,tipo);
            event.preventDefault();
        }
    }


    //comentario por si no funciona ctrl  z
    //funcion que busca el predio de forma global
    async function buscarPredioGlobal(){
        const clave=document.getElementById('input-predio-global').value;

        const tipo=document.querySelector('input[name="tipo-busqueda"]:checked').value;
        try{
            let response;
            
            response=await fetch(`/buscar_predio_global?clave=${clave}&pc=${tipo}`);

            const data = await response.json();
            console.log("Parámetro no reconocido:", data);  ////comenta
            if (data.error){
                alert(data.error);
                return;
            }
            if (marcadoresLayer) map.removeLayer(marcadoresLayer);

            marcadoresLayer= L.geoJSON(data,{
                style:{
                    color:'#FF0000',
                    weight:3,
                    fillColor: '#FF4500',
                    fillOpacity: 0.4
                },
                onEachFeature: function(feature, layer){
                // Verificar si la propiedad "nombre_delegacion" existe en el feature
                if (feature.properties ) {
                    const tooltipContent=`
                        <strong>Clave:</strong> ${feature.properties.clave}<br>
                        <strong>Colonia:</strong> ${feature.properties.colonia}<br>
                        <strong>Manzana:</strong> ${feature.properties.manzana}<br>
                        <strong>Delegación:</strong> ${feature.properties.delegacion}
                        `;
                    // Agregar un tooltip con el nombre de la propiedad
                    layer.bindTooltip(tooltipContent, {
                        permanent: false, // El tooltip no es permanente (solo se muestra al pasar el mouse)
                        direction: 'top', // Dirección del tooltip
                        className: 'custom-tooltip' // Clase CSS personalizada (opcional)
                    }); layer.on('dblclick', function(e) {
                        mostrarInfoPredio(feature.properties.clave,feature.properties.delegacion);
                        L.DomEvent.stopPropagation(e); // Evitar propagación del evento
                    });
                }
            }
            }).addTo(map);
            map.fitBounds(marcadoresLayer.getBounds());
        }catch(error){
            console.error('Error:',error);
            alert('Erro en la busqueda');
        }
    }
    async function toggleSubmenu() {
        const menus = document.getElementById('tickets-submenu');
        menus.classList.toggle('show-menu');
        if (menus.classList.contains('show-menu')){
            await cargarFolios();
        }
       // menus.classlist.toggle('show-meu',!wasOpen);
    }
    async function  cargarFolios() {
        console.log('usuario es admin:', usuarioEsAdmin);
        try{
            const response=await  fetch('/get_tickets');
            const tickets = await response.json();   
            const  container=  document.getElementById('folios-list');
            container.innerHTML= `
            <div class="form-group">
                <input type="text" 
                  placeholder="busca ticket" 
                    id="input-busqueda"
                    class="search-input" 
            </div>
                    `;
            
            if(usuarioEsAdmin){
            let usuarios=[];
            const userResponse=  await  fetch('/get_users');
            usuarios=   await  userResponse.json();
            console.log(usuarios);
            usuarios.forEach(us=>{
                const  div  =document.createElement('div');
                div.className='folio-item';
               div.innerHTML=`
                <strong>No  de Ticket:</strong> ${us.username}`;
            });

      
            //const formularioHTML = `   sin funcionalidad
            //<div class="form-group">
            //    <input type="text" 
            //      placeholder="${placeholders[tipo]}" 
            //        id="input-busqueda"
            //        class="search-input"
            //        onkeypress="manejarEnter(event,'${delegacion}','${tipo}')">
            //    <button onclick="realizarBusqueda('${delegacion}', '${tipo}')" class="search-button"> Buscar </button>
            //</div>`;


            


            tickets.forEach(tickett =>{
                const  div  =document.createElement('div');
                div.className='folio-item';
                div.innerHTML=`
        
                <strong>No  de Ticket:</strong> ${tickett.ticket}
                <div class="ticket-details" style="display:none;">
                    <div class="detail-item"><strong>Folio:</strong> ${tickett.folio || 'Sin datos' }</div>
                    <div  class="detail-item"><strong>Fecha de registro:</Strong>  ${tickett.fecha_proceso || '' } </div> 
                    <div class="detail-item"><strong>Cuenta:</strong> ${tickett.cuenta || 'Sin datos'}</div>
                    <div class="detail-item"><strong>Tarea:</strong> ${tickett.tarea  || 'Sin datos'}</div>
                    <div class="detail-item"><strong>Error:</strong> ${tickett.error  || 'Sin datos'}</div>
                    <div class="detail-item">
                        <span class="status-indicator ${tickett.status === 'resuelto' ? 'resuelto' : 'no-resuelto'}"></span>
                        Estado: ${tickett.status || 'no resuelto'}
                    </div>
                    <div class="detail-item">
                        Asignado a: ${tickett.assigned_to || 'Sin asignar'}
                    </div>
                </div>                 
            `;  
                div.addEventListener('click',function(){
                    const  details=this.querySelector('.ticket-details');
                    details.style.display=details.style.display==='none' ? 'block' : 'none';
                    console.log('ticket',tickett.ticket );
                    if (usuarioEsAdmin){
                        mostrarControlesAdmin( div,tickett,usuarios)
                  };
                });
                container.appendChild(div);
            });
        }
        else{
        tickets.forEach(tickett =>{
            const  div  =document.createElement('div');
            div.className='folio-item';
            div.innerHTML=`
            <strong>No  de Ticket:</strong> ${tickett.ticket}
            <div class="ticket-details" style="display:none;">
                <div class="detail-item"><strong>Folio:</strong> ${tickett.folio || 'Sin datos' }</div>
                <div  class="detail-item"><strong>Fecha de registro:</Strong>  ${tickett.fecha_proceso || '' } </div> 
                <div class="detail-item"><strong>Cuenta:</strong> ${tickett.cuenta || 'Sin datos'}</div>
                <div class="detail-item"><strong>Tarea:</strong> ${tickett.tarea  || 'Sin datos'}</div>
                <div class="detail-item"><strong>Error:</strong> ${tickett.error  || 'Sin datos'}</div>
                <div class="detail-item">
                    <span class="status-indicator ${tickett.status === 'resuelto' ? 'resuelto' : 'no-resuelto'}"></span>
                    Estado: ${tickett.status || 'no resuelto'}
                </div>
                <div class="detail-item">
                    Asignado a: ${tickett.assigned_to || 'Sin asignar'}
                </div>
            </div>                 
        `;  
            div.addEventListener('click',function(){
                const  details=this.querySelector('.ticket-details');
                details.style.display=details.style.display==='none' ? 'block' : 'none';
                console.log('ticket',tickett.ticket );
                if (usuarioEsAdmin){
                    mostrarControlesAdmin( div,tickett,usuarios)
              };
            });
            container.appendChild(div);
        });
        }
        } catch(error){
            console.error('error  al cargar tickets:', error);
        }
        
     }
        
    //funcion paara realizar busqueda

    async function realizarBusqueda(delegacion, tipo) {
         const valor = document.getElementById('input-busqueda').value;
         //if (tipo === 'predio') delegacion = 'any';

        try {
            // Limpiar resultados anteriores
            if (marcadoresLayer) map.removeLayer(marcadoresLayer);

            // Cargar geometría base
            await loadDelegacionGeometry(delegacion);

            // Obtener datos específicos
            const response = await fetch(`/buscar?delegacion=${delegacion}&tipo=${tipo}&valor=${valor}`);
            const data = await response.json();

            // Mapeo de colores según el tipo
            const coloresPorTipo = {
            'colonia': { color: '#90EE90', fillColor: '#32CD32' }, // Verde claro y verde intenso
            'manzana': { color: '#FFA500', fillColor: '#FFD700' }, // Naranja y dorado
            'predio': { color: '#87CEEB', fillColor: '#1E90FF' },
            'construccion':{ color: '#87CEEB', fillColor: '#1E90FF'},   // Azul claro y azul intenso
            'segmentacion':{ color: '#FF6347',illColor: '#DC143C'}       // Color del borde (Tomate, un tono de rojo)
            
        };

    // Obtener el estilo correspondiente al tipo
            const estilo = coloresPorTipo[tipo] || { color: '#000000', fillColor: '#FFFFFF' }; // Estilo por defecto

    // Procesar resultados
            marcadoresLayer = L.geoJSON(data, {
             style: {
            color: estilo.color,         // Color del borde
            weight: 2,                   // Grosor del borde
            fillColor: estilo.fillColor, // Color de relleno
            fillOpacity: 0.14            // Opacidad del relleno
            },
            onEachFeature: function (feature, layer) {
            // Determinar qué propiedad mostrar en el tooltip según el tipo
            let propiedadTooltip;
            switch (tipo) {
                case 'colonia':
                    propiedadTooltip = feature.properties.colonia || 'Sin nombre';
                    break;
                case 'manzana':
                    propiedadTooltip = feature.properties.TIPOMZA || 'Sin ID';
                    break;
                case 'construccion':
                    propiedadTooltip=feature.properties.bloque  || 'Sin ID';    
                    break;
                case 'predio':
                    propiedadTooltip = feature.properties.fid || 'Sin nombre';   //feature.properties.fid 
                    layer.on('dblclick', function(e) {
                        mostrarInfoPredio(propiedadTooltip,delegacion);
                        L.DomEvent.stopPropagation(e); // Evitar propagación del evento
                    });
                    break;
                case 'segmentacion':
                    propiedadTooltip=feature.properties.fid || 'Sin nombre' ;
                    layer.on('dblclick', function(e) {
                        mostrarInfoPredio(propiedadTooltip,delegacion);
                        L.DomEvent.stopPropagation(e); // Evitar propagación del evento
                    });
                    break;
                default:
                    propiedadTooltip = 'Sin información';
            }

            // Agregar un tooltip con la propiedad correspondiente
            if (feature.properties  && propiedadTooltip) {
                layer.bindTooltip(propiedadTooltip, {
                    permanent: false, // El tooltip no es permanente (solo se muestra al pasar el mouse)
                    direction: 'top', // Dirección del tooltip
                    className: 'custom-tooltip' // Clase CSS personalizada (opcional)
                });
            }
            }
           }).addTo(map);
        map.fitBounds(marcadoresLayer.getBounds());

        map.on('click', function(e) {
        if(!e.originalEvent.target.closest('#info-predio-container')) {
            cerrarInfoPredio();
            }
        });
        } catch (error) {
        console.error('Error al realizar la búsqueda:', error);
        }
    }



    function mostrarInfoPredio(fid,delegacion) {
        const container = document.getElementById('info-predio-container');
        const iframe = document.getElementById('info-predio');

        iframe.src = `/predio?fid=${fid}&del=${delegacion}`;
        container.style.display = 'block';
        }

    function cerrarInfoPredio() {
        document.getElementById('info-predio-container').style.display = 'none';
        document.getElementById('info-predio').src = '';
        }

    // funcion para cargar los datos
    async function loadDelegacionGeometry(delegacion) {
      try {
    // Eliminar capa anterior si existel
          if (delegacionLayer) {map.removeLayer(delegacionLayer);}

    
    //cuando se lla ma  funcion no hace nada
    // Fetch específico para delegaciones
            const response = await fetch(`/get_delegacion?nombre=${encodeURIComponent(delegacion)}`);
            if (!response.ok) throw new Error('Error en la respuesta');
    
            const data = await response.json();
    
    // Crear capa con estilo y tooltip
            delegacionLayer = L.geoJSON(data, {
                style: {
                    color: '#800000',
                    weight: 2,
                    fillColor: 'bd6568',
                    fillOpacity: 0.2
                },
                onEachFeature: function(feature, layer) {
                // Verificar si la propiedad "nombre_delegacion" existe en el feature
                if (feature.properties && feature.properties.NOMGEO) {
                    // Agregar un tooltip con el nombre de la delegación
                    layer.bindTooltip(feature.properties.NOMGEO, {
                        permanent: false, // El tooltip no es permanente (solo se muestra al pasar el mouse)
                        direction: 'top', // Dirección del tooltip
                        className: 'custom-tooltip' // Clase CSS personalizada (opcional)
                    });
                }
            }
    }).addTo(map);

    // Ajustar la vista al polígono
    map.fitBounds(delegacionLayer.getBounds());

     } catch (error) {
          console.error('Error al cargar la delegación:', error);
        alert('No se pudo cargar la delegación seleccionada');
      } 
    }

    // Función para cambiar la capa
    function setLayer(type) {
        if (layers[type]) {
            map.eachLayer(layer => map.removeLayer(layer)); // Quitar las capas actuales
            layers[type].addTo(map); // Agregar la nueva capa
            //cdmxPolygon.addTo(map);
            loadPolygons();
             // Volver a agregar el polígono
        } else {
            console.error('Tipo de capa no válido:', type);
        }
    }


    // nuevas  funciones 

    // Alternar visibilidad del menú
document.getElementById('menu-button').addEventListener('click', function() {
    document.getElementById('side-menu').classList.toggle('active');
});

// Cerrar el menú al hacer clic fuera de él
document.addEventListener('click', function(event) {
    var menu = document.getElementById('side-menu');
    var button = document.getElementById('menu-button');
    if (!menu.contains(event.target) && event.target !== button) {
        menu.classList.remove('active');
    }
});

// Funciones para las opciones del menú
function controlTickets() {
    toggleSubmenu(); // Reutiliza la función existente para mostrar tickets
    document.getElementById('side-menu').classList.remove('active'); // Cierra el menú
}

function resolucionTickets() {
    alert('Función para Resolución de Tickets aún no implementada');
    document.getElementById('side-menu').classList.remove('active'); // Cierra el menú
    // Aquí puedes agregar lógica adicional, como cargar un formulario o redirigir
}

function anadirCapas() {
    // Ejemplo: Alternar entre capas disponibles
    const currentLayer = map.hasLayer(layers.topographic) ? 'topographic' :
                         map.hasLayer(layers.satellite) ? 'satellite' : 'openstreet';
    if (currentLayer === 'topographic') setLayer('satellite');
    else if (currentLayer === 'satellite') setLayer('openstreet');
    else setLayer('topographic');
    document.getElementById('side-menu').classList.remove('active'); // Cierra el menú
}


//nuevas funciones para  controles de administrador a tickets   


function mostrarControlesAdmin(div, ticket, usuarios) {
    //console.log('mostrar  controlesaDmin  par ticket :',ticket,usuarios);
    //console.log(details)
    if (!div){
        console.error("Error:  contenedor no valido");
        return;
    }

    const details = div.querySelector('.ticket-details');  //esta parrte o se quita 

    if(!details){
        console.error("contenedro  sin elelmentos");
        return;
    }
    

    const  oldControl=details.querySelectorAll('.status-control,  assign-control');
    oldControl.forEach(control  =>   control.remove());


    
    // Selector de Estado
    const statusDiv = document.createElement('div');
    statusDiv.className = 'detail-item    status-control';
    statusDiv.innerHTML = `
        <strong>Estado:</strong>
        <select class="status-selector">
            <option value="no resuelto" ${ticket.status === 'no resuelto' ? 'selected' : ''}>No Resuelto</option>
            <option value="resuelto" ${ticket.status === 'resuelto' ? 'selected' : ''}>Resuelto</option>
        </select>
    `;
    
    // Selector de Asignación
    const assignDiv = document.createElement('div');
    assignDiv.className = 'detail-item     status-control';
    assignDiv.innerHTML = `
        <strong>Asignado a:</strong>
        <select class="assign-selector">
            <option value="sin asignar">Sin asignar</option>
            ${usuarios.map(user => `
                <option value="${user}" ${ticket.assigned_to === user ? 'selected' : ''}>
                    ${user}
                </option>
            `).join('')}
        </select>
    `;

    // Agregar eventos
    
    statusDiv.querySelector('select').addEventListener('click', (e) => {
        e.stopPropagation(); 
        console.log('mostrar  controles :',ticket.ticket,'status',e.target.value);  //actualizarTicket(ticket.ticket,'status', e.target.value); 
        actualizarTicket(ticket.ticket,'status', e.target.value);
       // e.stopPropagation();  
    });  
   
    assignDiv.querySelector('select').addEventListener('click', (e) => {
         e.stopPropagation();  //actualizarTicket(ticket.ticket,'assigned_to',e.target.value);
         console.log('mostrar opciones',ticket.ticket,'assigned_to',e.target.value);
         actualizarTicket(ticket.ticket,'assigned_to',e.target.value);
         //e.stopPropagation();
         
    });
    

    // Insertar antes del último elemento
    //details.insertBefore(statusDiv, details.lastElementChild);    // conetos   la funcion  hace el trabajo
    details.appendChild(statusDiv);

    //details.insertBefore(assignDiv,details.lastElementChild);     ///con esto la funcion   funciona d forma correcta
    details.appendChild(assignDiv);
    
}



async function actualizarTicket(ticket, campo, valor) {
    console.log('dtos:',ticket,campo, valor )
    try {
        const response = await fetch('/update_ticket', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                ticket: ticket,
                [campo]: valor,
                [campo]:valor
            })
        });

        const resultado = await response.json();
        
        if (!response.ok) {
            throw new Error(resultado.error || 'Error al actualizar');
        }

        // Actualizar UI
        //const ticketElement = document.querySelector(`.folio-item:has([data-ticket-id="${ticket}"])`);
        //if (ticketElement) {
        //    if (campo === 'status') {
        //        ticketElement.querySelector('.status-selector').value = valor;
        //        ticketElement.querySelector('.status-indicator').className = `status-indicator ${valor === 'resuelto' ? 'resuelto' : 'no-resuelto'}`;
        //    } else {
        //        ticketElement.querySelector('.assign-selector').value = valor;
        //  }
        //}

        // Mostrar confirmación
        const confirmation = document.createElement('div');
        confirmation.textContent = '✅ Cambios guardados';
        confirmation.style.cssText = 'position:fixed; top:20px; right:20px; color:green; z-index:9999;';
        document.body.appendChild(confirmation);
        setTimeout(() => confirmation.remove(), 2000);

    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar los cambios');
    }
}

