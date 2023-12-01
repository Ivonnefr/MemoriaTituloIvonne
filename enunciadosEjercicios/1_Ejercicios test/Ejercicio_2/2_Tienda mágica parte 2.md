Hablando con el dueño de la tienda, descubrimos otras necesidades:
* Una vez que `diaRestante` llega a 0 para un artículo, su calidad baja el doble de rápido para cada día siguiente.
* Una vez que la calidad de un artículo (y por tanto su valor) desciende a 0, debe retirarse de la tienda.
* Existe una subcategoría de artículos (clase `ArticuloComun`) que no puede tener una calidad superior a 50.
* El constructor de `ArticuloComun` utiliza los mismos argumentos que para un `Articulo`.
* Los artículos se compran al 40% de su valor.

Proporcione las clases y su código para satisfacer estas necesidades.